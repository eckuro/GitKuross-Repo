"""Tests for alert rules engine."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from oslo_insider_alerts.config import AlertThresholds
from oslo_insider_alerts.models import (
    AlertType,
    Company,
    CompanySize,
    Insider,
    InsiderRole,
    InsiderTransaction,
    TransactionType,
)
from oslo_insider_alerts.rules import (
    AlertRulesEngine,
    LargeSingleTransactionRule,
    HighPercentageTradeRule,
    AggregateActivityRule,
    InsiderClusterRule,
)


@pytest.fixture
def thresholds() -> AlertThresholds:
    """Create test thresholds."""
    return AlertThresholds(
        min_transaction_value_nok=500000,
        min_shares_percent=0.1,
        aggregate_value_nok=2000000,
        aggregate_window_days=7,
        min_insider_count=2,
    )


@pytest.fixture
def test_company() -> Company:
    """Create a test company."""
    return Company(
        ticker="TEST",
        name="Test Company ASA",
        market_cap_nok=Decimal("2000000000"),
        shares_outstanding=10000000,
        size_classification=CompanySize.SMALL,
    )


def create_transaction(
    company: Company,
    insider_name: str = "Test Insider",
    tx_type: TransactionType = TransactionType.BUY,
    shares: int = 10000,
    price: Decimal = Decimal("100"),
    days_ago: int = 0,
    tx_id: str = "tx-001",
) -> InsiderTransaction:
    """Helper to create transactions."""
    tx_date = datetime.now() - timedelta(days=days_ago)
    return InsiderTransaction(
        id=tx_id,
        company=company,
        insider=Insider(name=insider_name, role=InsiderRole.CEO),
        transaction_type=tx_type,
        transaction_date=tx_date,
        publication_date=tx_date,
        shares=shares,
        price_per_share_nok=price,
        total_value_nok=Decimal(shares) * price,
    )


class TestLargeSingleTransactionRule:
    """Tests for LargeSingleTransactionRule."""

    def test_triggers_above_threshold(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that rule triggers for transactions above threshold."""
        rule = LargeSingleTransactionRule(thresholds)

        # Transaction of 600,000 NOK (above 500,000 threshold)
        transaction = create_transaction(
            test_company, shares=6000, price=Decimal("100")
        )

        alert = rule.evaluate(transaction, [])
        assert alert is not None
        assert alert.alert_type == AlertType.LARGE_SINGLE_TRANSACTION

    def test_no_trigger_below_threshold(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that rule does not trigger below threshold."""
        rule = LargeSingleTransactionRule(thresholds)

        # Transaction of 400,000 NOK (below 500,000 threshold)
        transaction = create_transaction(
            test_company, shares=4000, price=Decimal("100")
        )

        alert = rule.evaluate(transaction, [])
        assert alert is None


class TestHighPercentageTradeRule:
    """Tests for HighPercentageTradeRule."""

    def test_triggers_above_percent_threshold(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that rule triggers for high percentage trades."""
        rule = HighPercentageTradeRule(thresholds)

        # 0.2% of shares (above 0.1% threshold)
        # 10M shares outstanding, so 20,000 = 0.2%
        transaction = create_transaction(
            test_company, shares=20000, price=Decimal("100")
        )

        alert = rule.evaluate(transaction, [])
        assert alert is not None
        assert alert.alert_type == AlertType.HIGH_PERCENTAGE_TRADE

    def test_no_trigger_below_percent_threshold(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that rule does not trigger below percentage threshold."""
        rule = HighPercentageTradeRule(thresholds)

        # 0.05% of shares (below 0.1% threshold)
        # 10M shares outstanding, so 5,000 = 0.05%
        transaction = create_transaction(
            test_company, shares=5000, price=Decimal("100")
        )

        alert = rule.evaluate(transaction, [])
        assert alert is None


class TestAggregateActivityRule:
    """Tests for AggregateActivityRule."""

    def test_triggers_on_aggregate_threshold(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that rule triggers when aggregate exceeds threshold."""
        rule = AggregateActivityRule(thresholds)

        # Create historical transactions totaling 1.5M
        historical = [
            create_transaction(
                test_company, shares=10000, price=Decimal("100"), days_ago=2, tx_id="h1"
            ),  # 1M
            create_transaction(
                test_company, shares=5000, price=Decimal("100"), days_ago=1, tx_id="h2"
            ),  # 0.5M
        ]

        # New transaction of 600K pushes total to 2.1M (above 2M threshold)
        new_tx = create_transaction(
            test_company, shares=6000, price=Decimal("100"), tx_id="new"
        )

        alert = rule.evaluate(new_tx, historical)
        assert alert is not None
        assert alert.alert_type == AlertType.AGGREGATE_ACTIVITY


class TestInsiderClusterRule:
    """Tests for InsiderClusterRule."""

    def test_triggers_on_multiple_insiders(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that rule triggers when multiple insiders trade."""
        rule = InsiderClusterRule(thresholds)

        # One insider already bought
        historical = [
            create_transaction(
                test_company,
                insider_name="Insider A",
                shares=5000,
                price=Decimal("100"),
                days_ago=2,
                tx_id="h1",
            ),
        ]

        # Second insider buys, should trigger cluster alert
        new_tx = create_transaction(
            test_company,
            insider_name="Insider B",
            shares=5000,
            price=Decimal("100"),
            tx_id="new",
        )

        alert = rule.evaluate(new_tx, historical)
        assert alert is not None
        assert alert.alert_type == AlertType.INSIDER_CLUSTER


class TestAlertRulesEngine:
    """Tests for AlertRulesEngine."""

    def test_engine_evaluates_all_rules(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that engine evaluates all rules."""
        engine = AlertRulesEngine(thresholds)

        # Transaction that triggers large transaction rule
        transaction = create_transaction(
            test_company, shares=10000, price=Decimal("100")  # 1M NOK
        )

        alerts = engine.evaluate_transaction(transaction)
        assert len(alerts) >= 1

    def test_engine_tracks_history(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that engine maintains transaction history."""
        engine = AlertRulesEngine(thresholds)

        tx1 = create_transaction(test_company, tx_id="tx1")
        tx2 = create_transaction(test_company, tx_id="tx2")

        engine.evaluate_transaction(tx1)
        engine.evaluate_transaction(tx2)

        stats = engine.get_summary_stats()
        assert stats["total_transactions"] == 2

    def test_engine_deduplicates_transactions(
        self, thresholds: AlertThresholds, test_company: Company
    ) -> None:
        """Test that engine doesn't process same transaction twice."""
        engine = AlertRulesEngine(thresholds)

        transaction = create_transaction(test_company, tx_id="tx1")

        alerts1 = engine.evaluate_transaction(transaction)
        alerts2 = engine.evaluate_transaction(transaction)  # Same transaction

        # Second evaluation should return no alerts (already processed)
        assert len(alerts2) == 0
