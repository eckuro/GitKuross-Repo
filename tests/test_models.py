"""Tests for data models."""

from datetime import datetime
from decimal import Decimal

import pytest

from oslo_insider_alerts.models import (
    Alert,
    AlertSeverity,
    AlertType,
    Company,
    CompanySize,
    Insider,
    InsiderRole,
    InsiderTransaction,
    TransactionType,
)


@pytest.fixture
def sample_company() -> Company:
    """Create a sample company for testing."""
    return Company(
        ticker="TEST",
        name="Test Company ASA",
        isin="NO0000000001",
        market_cap_nok=Decimal("2000000000"),  # 2 billion NOK
        shares_outstanding=10000000,
        size_classification=CompanySize.SMALL,
    )


@pytest.fixture
def sample_insider() -> Insider:
    """Create a sample insider for testing."""
    return Insider(
        name="John Doe",
        role=InsiderRole.CEO,
        role_description="Chief Executive Officer",
    )


@pytest.fixture
def sample_transaction(sample_company: Company, sample_insider: Insider) -> InsiderTransaction:
    """Create a sample transaction for testing."""
    return InsiderTransaction(
        id="tx-001",
        company=sample_company,
        insider=sample_insider,
        transaction_type=TransactionType.BUY,
        transaction_date=datetime(2024, 1, 15, 10, 30),
        publication_date=datetime(2024, 1, 15, 12, 0),
        shares=50000,
        price_per_share_nok=Decimal("100.50"),
        total_value_nok=Decimal("5025000"),
        shares_after_transaction=150000,
        source_url="https://example.com/announcement/123",
    )


class TestCompany:
    """Tests for Company model."""

    def test_company_creation(self, sample_company: Company) -> None:
        """Test company creation with all fields."""
        assert sample_company.ticker == "TEST"
        assert sample_company.name == "Test Company ASA"
        assert sample_company.market_cap_nok == Decimal("2000000000")

    def test_company_hash(self, sample_company: Company) -> None:
        """Test company hashing for use in sets/dicts."""
        company_set = {sample_company}
        assert sample_company in company_set


class TestInsider:
    """Tests for Insider model."""

    def test_insider_creation(self, sample_insider: Insider) -> None:
        """Test insider creation."""
        assert sample_insider.name == "John Doe"
        assert sample_insider.role == InsiderRole.CEO

    def test_insider_hash(self, sample_insider: Insider) -> None:
        """Test insider hashing."""
        insider_set = {sample_insider}
        assert sample_insider in insider_set


class TestInsiderTransaction:
    """Tests for InsiderTransaction model."""

    def test_transaction_creation(self, sample_transaction: InsiderTransaction) -> None:
        """Test transaction creation."""
        assert sample_transaction.id == "tx-001"
        assert sample_transaction.shares == 50000
        assert sample_transaction.total_value_nok == Decimal("5025000")

    def test_shares_percent_calculation(self, sample_transaction: InsiderTransaction) -> None:
        """Test shares percentage calculation."""
        # 50000 shares out of 10000000 = 0.5%
        assert sample_transaction.shares_percent == pytest.approx(0.5, rel=0.01)

    def test_shares_percent_without_outstanding(
        self, sample_company: Company, sample_insider: Insider
    ) -> None:
        """Test shares percentage when outstanding shares not available."""
        company_no_shares = Company(
            ticker="TEST2",
            name="Test Company 2",
            shares_outstanding=None,
        )
        transaction = InsiderTransaction(
            id="tx-002",
            company=company_no_shares,
            insider=sample_insider,
            transaction_type=TransactionType.BUY,
            transaction_date=datetime.now(),
            publication_date=datetime.now(),
            shares=1000,
            price_per_share_nok=Decimal("50"),
            total_value_nok=Decimal("50000"),
        )
        assert transaction.shares_percent is None


class TestAlert:
    """Tests for Alert model."""

    def test_alert_creation(
        self, sample_company: Company, sample_transaction: InsiderTransaction
    ) -> None:
        """Test alert creation."""
        alert = Alert(
            id="alert-001",
            alert_type=AlertType.LARGE_SINGLE_TRANSACTION,
            severity=AlertSeverity.HIGH,
            company=sample_company,
            transactions=[sample_transaction],
            title="Large Trade Alert",
            summary="Test alert summary",
        )

        assert alert.id == "alert-001"
        assert alert.severity == AlertSeverity.HIGH
        assert len(alert.transactions) == 1

    def test_alert_format_console(
        self, sample_company: Company, sample_transaction: InsiderTransaction
    ) -> None:
        """Test console formatting."""
        alert = Alert(
            id="alert-001",
            alert_type=AlertType.LARGE_SINGLE_TRANSACTION,
            severity=AlertSeverity.HIGH,
            company=sample_company,
            transactions=[sample_transaction],
            title="Large Trade Alert",
            summary="Test alert summary",
        )

        formatted = alert.format_console()
        assert "Large Trade Alert" in formatted
        assert "TEST" in formatted

    def test_alert_format_slack(
        self, sample_company: Company, sample_transaction: InsiderTransaction
    ) -> None:
        """Test Slack formatting."""
        alert = Alert(
            id="alert-001",
            alert_type=AlertType.LARGE_SINGLE_TRANSACTION,
            severity=AlertSeverity.HIGH,
            company=sample_company,
            transactions=[sample_transaction],
            title="Large Trade Alert",
            summary="Test alert summary",
        )

        slack_payload = alert.format_slack()
        assert "blocks" in slack_payload
        assert len(slack_payload["blocks"]) > 0
