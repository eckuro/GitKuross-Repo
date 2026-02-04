"""Database layer for persisting transactions and alerts."""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class TransactionRecord(Base):
    """Database model for insider transactions."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_ticker: Mapped[str] = mapped_column(String(20), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    company_isin: Mapped[str] = mapped_column(String(20), default="")
    insider_name: Mapped[str] = mapped_column(String(255), index=True)
    insider_role: Mapped[str] = mapped_column(String(50))
    transaction_type: Mapped[str] = mapped_column(String(20))
    transaction_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    publication_date: Mapped[datetime] = mapped_column(DateTime)
    shares: Mapped[int] = mapped_column(Integer)
    price_per_share_nok: Mapped[float] = mapped_column(Float)
    total_value_nok: Mapped[float] = mapped_column(Float, index=True)
    shares_after_transaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), default="")
    raw_data: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AlertRecord(Base):
    """Database model for generated alerts."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_type: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    company_ticker: Mapped[str] = mapped_column(String(20), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    transaction_ids: Mapped[str] = mapped_column(Text)  # JSON list of transaction IDs
    metrics: Mapped[str] = mapped_column(Text, default="{}")  # JSON metrics
    triggered_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CompanyCache(Base):
    """Cache for company market data."""

    __tablename__ = "company_cache"

    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    isin: Mapped[str] = mapped_column(String(20), default="")
    market_cap_nok: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shares_outstanding: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    size_classification: Mapped[str] = mapped_column(String(20), default="unknown")
    sector: Mapped[str] = mapped_column(String(100), default="")
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Database:
    """Async database interface for the application."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._engine = None
        self._session_factory = None

    async def initialize(self) -> None:
        """Initialize the database connection and create tables."""
        self._engine = create_async_engine(self.database_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()

    def _get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory()

    async def save_transaction(self, transaction: "InsiderTransaction") -> None:
        """Save a transaction to the database.

        Args:
            transaction: The transaction to save
        """
        from .models import InsiderTransaction

        async with self._get_session() as session:
            # Check if already exists
            existing = await session.get(TransactionRecord, transaction.id)
            if existing:
                return

            record = TransactionRecord(
                id=transaction.id,
                company_ticker=transaction.company.ticker,
                company_name=transaction.company.name,
                company_isin=transaction.company.isin,
                insider_name=transaction.insider.name,
                insider_role=transaction.insider.role.value,
                transaction_type=transaction.transaction_type.value,
                transaction_date=transaction.transaction_date,
                publication_date=transaction.publication_date,
                shares=transaction.shares,
                price_per_share_nok=float(transaction.price_per_share_nok),
                total_value_nok=float(transaction.total_value_nok),
                shares_after_transaction=transaction.shares_after_transaction,
                source_url=transaction.source_url,
                raw_data=json.dumps(transaction.raw_data),
            )

            session.add(record)
            await session.commit()

    async def save_transactions(self, transactions: list["InsiderTransaction"]) -> int:
        """Save multiple transactions to the database.

        Args:
            transactions: List of transactions to save

        Returns:
            Number of new transactions saved
        """
        saved_count = 0

        async with self._get_session() as session:
            for tx in transactions:
                existing = await session.get(TransactionRecord, tx.id)
                if existing:
                    continue

                record = TransactionRecord(
                    id=tx.id,
                    company_ticker=tx.company.ticker,
                    company_name=tx.company.name,
                    company_isin=tx.company.isin,
                    insider_name=tx.insider.name,
                    insider_role=tx.insider.role.value,
                    transaction_type=tx.transaction_type.value,
                    transaction_date=tx.transaction_date,
                    publication_date=tx.publication_date,
                    shares=tx.shares,
                    price_per_share_nok=float(tx.price_per_share_nok),
                    total_value_nok=float(tx.total_value_nok),
                    shares_after_transaction=tx.shares_after_transaction,
                    source_url=tx.source_url,
                    raw_data=json.dumps(tx.raw_data),
                )

                session.add(record)
                saved_count += 1

            await session.commit()

        return saved_count

    async def get_recent_transactions(
        self,
        days: int = 30,
        company_ticker: Optional[str] = None,
    ) -> list[TransactionRecord]:
        """Get recent transactions from the database.

        Args:
            days: Number of days to look back
            company_ticker: Optional filter by company

        Returns:
            List of transaction records
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        async with self._get_session() as session:
            query = select(TransactionRecord).where(
                TransactionRecord.transaction_date >= cutoff
            )

            if company_ticker:
                query = query.where(TransactionRecord.company_ticker == company_ticker)

            query = query.order_by(TransactionRecord.transaction_date.desc())

            result = await session.execute(query)
            return list(result.scalars().all())

    async def save_alert(self, alert: "Alert") -> None:
        """Save an alert to the database.

        Args:
            alert: The alert to save
        """
        async with self._get_session() as session:
            record = AlertRecord(
                id=alert.id,
                alert_type=alert.alert_type.value,
                severity=alert.severity.value,
                company_ticker=alert.company.ticker,
                company_name=alert.company.name,
                title=alert.title,
                summary=alert.summary,
                transaction_ids=json.dumps([tx.id for tx in alert.transactions]),
                metrics=json.dumps(alert.metrics),
                triggered_at=alert.triggered_at,
                notified=False,
            )

            session.add(record)
            await session.commit()

    async def mark_alert_notified(self, alert_id: str) -> None:
        """Mark an alert as notified.

        Args:
            alert_id: The alert ID
        """
        async with self._get_session() as session:
            alert = await session.get(AlertRecord, alert_id)
            if alert:
                alert.notified = True
                await session.commit()

    async def get_unnotified_alerts(self) -> list[AlertRecord]:
        """Get alerts that haven't been sent yet.

        Returns:
            List of unnotified alert records
        """
        async with self._get_session() as session:
            query = select(AlertRecord).where(
                AlertRecord.notified == False  # noqa: E712
            ).order_by(AlertRecord.triggered_at)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_transaction_ids(self) -> set[str]:
        """Get all transaction IDs in the database.

        Returns:
            Set of transaction IDs
        """
        async with self._get_session() as session:
            query = select(TransactionRecord.id)
            result = await session.execute(query)
            return set(result.scalars().all())

    async def update_company_cache(
        self,
        ticker: str,
        name: str,
        market_cap_nok: Optional[float] = None,
        shares_outstanding: Optional[int] = None,
        size_classification: str = "unknown",
    ) -> None:
        """Update the company cache.

        Args:
            ticker: Company ticker
            name: Company name
            market_cap_nok: Market cap in NOK
            shares_outstanding: Shares outstanding
            size_classification: Size classification
        """
        async with self._get_session() as session:
            existing = await session.get(CompanyCache, ticker)

            if existing:
                existing.name = name
                if market_cap_nok is not None:
                    existing.market_cap_nok = market_cap_nok
                if shares_outstanding is not None:
                    existing.shares_outstanding = shares_outstanding
                existing.size_classification = size_classification
                existing.last_updated = datetime.utcnow()
            else:
                record = CompanyCache(
                    ticker=ticker,
                    name=name,
                    market_cap_nok=market_cap_nok,
                    shares_outstanding=shares_outstanding,
                    size_classification=size_classification,
                )
                session.add(record)

            await session.commit()

    async def get_company_cache(self, ticker: str) -> Optional[CompanyCache]:
        """Get cached company data.

        Args:
            ticker: Company ticker

        Returns:
            Cached company data or None
        """
        async with self._get_session() as session:
            return await session.get(CompanyCache, ticker)
