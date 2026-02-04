"""Main application that orchestrates the insider trading alert system."""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional

from rich.console import Console

from .classifier import CompanySizeClassifier
from .config import Settings
from .database import Database
from .fetcher import OsloBorsDataFetcher
from .models import (
    Alert,
    Company,
    CompanySize,
    Insider,
    InsiderRole,
    InsiderTransaction,
    TransactionType,
)
from .notifications import NotificationManager
from .rules import AlertRulesEngine


class InsiderAlertApp:
    """Main application for monitoring insider trading on Oslo Børs."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.console = Console()

        # Initialize components
        self.database: Optional[Database] = None
        self.fetcher: Optional[OsloBorsDataFetcher] = None
        self.classifier: Optional[CompanySizeClassifier] = None
        self.rules_engine: Optional[AlertRulesEngine] = None
        self.notification_manager: Optional[NotificationManager] = None

        self._running = False

    async def initialize(self) -> None:
        """Initialize all application components."""
        self.console.print("[blue]Initializing Oslo Insider Alerts...[/blue]")

        # Initialize database
        self.database = Database(self.settings.database_url)
        await self.database.initialize()

        # Initialize fetcher
        self.fetcher = OsloBorsDataFetcher(self.settings.data_source)

        # Initialize classifier
        self.classifier = CompanySizeClassifier(
            filter_config=self.settings.company_filter,
            fetcher=self.fetcher,
        )

        # Initialize rules engine
        self.rules_engine = AlertRulesEngine(self.settings.thresholds)

        # Initialize notification manager
        self.notification_manager = NotificationManager(self.settings.notifications)

        self.console.print("[green]Initialization complete.[/green]")

    async def shutdown(self) -> None:
        """Shut down the application cleanly."""
        self.console.print("[blue]Shutting down...[/blue]")
        self._running = False

        if self.notification_manager:
            await self.notification_manager.close()

        if self.database:
            await self.database.close()

        self.console.print("[green]Shutdown complete.[/green]")

    async def fetch_and_process(self, days_back: int = 7) -> list[Alert]:
        """Fetch new transactions and process them for alerts.

        Args:
            days_back: Number of days to look back for transactions

        Returns:
            List of generated alerts
        """
        if not self.fetcher or not self.classifier or not self.rules_engine:
            raise RuntimeError("Application not initialized")

        self.console.print(f"[blue]Fetching insider transactions (last {days_back} days)...[/blue]")

        all_alerts: list[Alert] = []

        async with self.fetcher:
            # Fetch transactions
            transactions = await self.fetcher.fetch_recent_insider_transactions(
                days_back=days_back,
                max_items=200,
            )

            self.console.print(f"[green]Fetched {len(transactions)} transactions[/green]")

            # Filter for target companies (small/medium cap)
            filtered_transactions: list[InsiderTransaction] = []

            for tx in transactions:
                is_target = await self.classifier.is_target_company_with_fetch(tx.company)
                if is_target:
                    filtered_transactions.append(tx)

            self.console.print(
                f"[green]{len(filtered_transactions)} transactions from small/medium cap companies[/green]"
            )

            # Save to database
            if self.database:
                saved = await self.database.save_transactions(filtered_transactions)
                self.console.print(f"[green]Saved {saved} new transactions to database[/green]")

            # Evaluate against alert rules
            alerts = self.rules_engine.evaluate_transactions(filtered_transactions)

            self.console.print(f"[yellow]Generated {len(alerts)} alerts[/yellow]")

            # Save alerts
            if self.database:
                for alert in alerts:
                    await self.database.save_alert(alert)

            all_alerts.extend(alerts)

        return all_alerts

    async def send_alerts(self, alerts: list[Alert]) -> None:
        """Send alerts through configured notification channels.

        Args:
            alerts: List of alerts to send
        """
        if not alerts:
            self.console.print("[dim]No alerts to send[/dim]")
            return

        if not self.notification_manager:
            raise RuntimeError("Application not initialized")

        self.console.print(f"[blue]Sending {len(alerts)} alerts...[/blue]")

        results = await self.notification_manager.send_alerts(alerts)

        for channel, count in results.items():
            self.console.print(f"[green]Sent {count}/{len(alerts)} alerts to {channel}[/green]")

        # Mark as notified in database
        if self.database:
            for alert in alerts:
                await self.database.mark_alert_notified(alert.id)

    async def run_once(self, days_back: int = 7) -> list[Alert]:
        """Run a single fetch and alert cycle.

        Args:
            days_back: Number of days to look back

        Returns:
            List of generated alerts
        """
        alerts = await self.fetch_and_process(days_back=days_back)
        await self.send_alerts(alerts)
        return alerts

    async def run_continuous(self) -> None:
        """Run continuously, checking for new transactions periodically."""
        self._running = True
        self.console.print(
            f"[blue]Starting continuous monitoring "
            f"(interval: {self.settings.poll_interval_minutes} minutes)...[/blue]"
        )

        while self._running:
            try:
                await self.run_once(days_back=1)  # Only look at last day for continuous mode

                # Wait for next poll
                self.console.print(
                    f"[dim]Next check in {self.settings.poll_interval_minutes} minutes...[/dim]"
                )
                await asyncio.sleep(self.settings.poll_interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.console.print(f"[red]Error during polling: {e}[/red]")
                # Wait before retrying
                await asyncio.sleep(60)

    async def get_stats(self) -> dict:
        """Get application statistics.

        Returns:
            Dictionary with various statistics
        """
        stats = {}

        if self.rules_engine:
            stats["rules_engine"] = self.rules_engine.get_summary_stats()

        if self.database:
            recent_txs = await self.database.get_recent_transactions(days=30)
            stats["database"] = {
                "recent_transactions_30d": len(recent_txs),
            }

        return stats


def convert_db_record_to_transaction(record) -> InsiderTransaction:
    """Convert a database record back to an InsiderTransaction model.

    Args:
        record: TransactionRecord from database

    Returns:
        InsiderTransaction model
    """
    import json

    company = Company(
        ticker=record.company_ticker,
        name=record.company_name,
        isin=record.company_isin,
    )

    insider = Insider(
        name=record.insider_name,
        role=InsiderRole(record.insider_role) if record.insider_role in [r.value for r in InsiderRole] else InsiderRole.OTHER,
    )

    return InsiderTransaction(
        id=record.id,
        company=company,
        insider=insider,
        transaction_type=TransactionType(record.transaction_type) if record.transaction_type in [t.value for t in TransactionType] else TransactionType.OTHER,
        transaction_date=record.transaction_date,
        publication_date=record.publication_date,
        shares=record.shares,
        price_per_share_nok=Decimal(str(record.price_per_share_nok)),
        total_value_nok=Decimal(str(record.total_value_nok)),
        shares_after_transaction=record.shares_after_transaction,
        source_url=record.source_url,
        raw_data=json.loads(record.raw_data) if record.raw_data else {},
    )
