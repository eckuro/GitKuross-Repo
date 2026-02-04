"""Alert rules engine for detecting heavy insider trading activity."""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from .config import AlertThresholds
from .models import (
    Alert,
    AlertSeverity,
    AlertType,
    InsiderTransaction,
    TransactionType,
)


class AlertRule:
    """Base class for alert rules."""

    name: str = "base_rule"

    def __init__(self, thresholds: AlertThresholds):
        self.thresholds = thresholds

    def evaluate(
        self,
        transaction: InsiderTransaction,
        historical_transactions: list[InsiderTransaction],
    ) -> Optional[Alert]:
        """Evaluate the rule against a transaction.

        Args:
            transaction: The new transaction to evaluate
            historical_transactions: Recent transactions for context

        Returns:
            Alert if rule triggers, None otherwise
        """
        raise NotImplementedError


class LargeSingleTransactionRule(AlertRule):
    """Alert on single transactions above a value threshold."""

    name = "large_single_transaction"

    def evaluate(
        self,
        transaction: InsiderTransaction,
        historical_transactions: list[InsiderTransaction],
    ) -> Optional[Alert]:
        threshold = Decimal(str(self.thresholds.min_transaction_value_nok))

        if transaction.total_value_nok < threshold:
            return None

        # Determine severity based on how much it exceeds threshold
        ratio = float(transaction.total_value_nok / threshold)
        if ratio >= 10:
            severity = AlertSeverity.CRITICAL
        elif ratio >= 5:
            severity = AlertSeverity.HIGH
        elif ratio >= 2:
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW

        direction = "purchased" if transaction.transaction_type == TransactionType.BUY else "sold"

        return Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.LARGE_SINGLE_TRANSACTION,
            severity=severity,
            company=transaction.company,
            transactions=[transaction],
            title=f"Large Insider Trade: {transaction.company.ticker}",
            summary=(
                f"{transaction.insider.name} ({transaction.insider.role.value}) {direction} "
                f"{transaction.shares:,} shares of {transaction.company.name} for "
                f"{transaction.total_value_nok:,.0f} NOK "
                f"(threshold: {self.thresholds.min_transaction_value_nok:,} NOK)"
            ),
            metrics={
                "transaction_value_nok": float(transaction.total_value_nok),
                "threshold_nok": self.thresholds.min_transaction_value_nok,
                "ratio": ratio,
            },
        )


class HighPercentageTradeRule(AlertRule):
    """Alert when transaction represents significant percentage of outstanding shares."""

    name = "high_percentage_trade"

    def evaluate(
        self,
        transaction: InsiderTransaction,
        historical_transactions: list[InsiderTransaction],
    ) -> Optional[Alert]:
        shares_percent = transaction.shares_percent

        if shares_percent is None:
            return None

        if shares_percent < self.thresholds.min_shares_percent:
            return None

        # Determine severity
        if shares_percent >= 1.0:
            severity = AlertSeverity.CRITICAL
        elif shares_percent >= 0.5:
            severity = AlertSeverity.HIGH
        elif shares_percent >= 0.25:
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW

        direction = "purchased" if transaction.transaction_type == TransactionType.BUY else "sold"

        return Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.HIGH_PERCENTAGE_TRADE,
            severity=severity,
            company=transaction.company,
            transactions=[transaction],
            title=f"High % Insider Trade: {transaction.company.ticker}",
            summary=(
                f"{transaction.insider.name} ({transaction.insider.role.value}) {direction} "
                f"{shares_percent:.3f}% of {transaction.company.name}'s outstanding shares "
                f"({transaction.shares:,} shares for {transaction.total_value_nok:,.0f} NOK)"
            ),
            metrics={
                "shares_percent": shares_percent,
                "threshold_percent": self.thresholds.min_shares_percent,
                "shares": transaction.shares,
            },
        )


class AggregateActivityRule(AlertRule):
    """Alert when aggregate insider activity exceeds threshold within time window."""

    name = "aggregate_activity"

    def evaluate(
        self,
        transaction: InsiderTransaction,
        historical_transactions: list[InsiderTransaction],
    ) -> Optional[Alert]:
        # Get transactions for the same company within the time window
        cutoff = datetime.now() - timedelta(days=self.thresholds.aggregate_window_days)

        same_company_txs = [
            tx for tx in historical_transactions
            if tx.company.ticker == transaction.company.ticker
            and tx.transaction_date >= cutoff
        ]

        # Include current transaction
        all_txs = same_company_txs + [transaction]

        # Calculate aggregate values by direction
        buy_total = sum(
            tx.total_value_nok for tx in all_txs
            if tx.transaction_type == TransactionType.BUY
        )
        sell_total = sum(
            tx.total_value_nok for tx in all_txs
            if tx.transaction_type == TransactionType.SELL
        )

        # Check against threshold
        threshold = Decimal(str(self.thresholds.aggregate_value_nok))

        # Alert if either direction exceeds threshold
        if buy_total >= threshold:
            direction = "buying"
            total = buy_total
            relevant_txs = [tx for tx in all_txs if tx.transaction_type == TransactionType.BUY]
        elif sell_total >= threshold:
            direction = "selling"
            total = sell_total
            relevant_txs = [tx for tx in all_txs if tx.transaction_type == TransactionType.SELL]
        else:
            return None

        # Only alert if this is a new threshold crossing
        # (Check if we would have alerted before this transaction)
        prev_total = total - transaction.total_value_nok
        if prev_total >= threshold:
            return None

        # Determine severity
        ratio = float(total / threshold)
        if ratio >= 5:
            severity = AlertSeverity.CRITICAL
        elif ratio >= 2:
            severity = AlertSeverity.HIGH
        else:
            severity = AlertSeverity.MEDIUM

        unique_insiders = len(set(tx.insider.name for tx in relevant_txs))

        return Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.AGGREGATE_ACTIVITY,
            severity=severity,
            company=transaction.company,
            transactions=relevant_txs,
            title=f"Heavy Aggregate Insider {direction.title()}: {transaction.company.ticker}",
            summary=(
                f"Aggregate insider {direction} in {transaction.company.name} has reached "
                f"{total:,.0f} NOK over the past {self.thresholds.aggregate_window_days} days "
                f"({unique_insiders} insider(s), {len(relevant_txs)} transaction(s))"
            ),
            metrics={
                "aggregate_value_nok": float(total),
                "threshold_nok": self.thresholds.aggregate_value_nok,
                "window_days": self.thresholds.aggregate_window_days,
                "transaction_count": len(relevant_txs),
                "unique_insiders": unique_insiders,
            },
        )


class InsiderClusterRule(AlertRule):
    """Alert when multiple insiders trade in the same direction."""

    name = "insider_cluster"

    def evaluate(
        self,
        transaction: InsiderTransaction,
        historical_transactions: list[InsiderTransaction],
    ) -> Optional[Alert]:
        # Get recent transactions for the same company
        cutoff = datetime.now() - timedelta(days=self.thresholds.aggregate_window_days)

        same_company_txs = [
            tx for tx in historical_transactions
            if tx.company.ticker == transaction.company.ticker
            and tx.transaction_date >= cutoff
        ]

        all_txs = same_company_txs + [transaction]

        # Group by direction and count unique insiders
        buyers = set()
        sellers = set()

        for tx in all_txs:
            if tx.transaction_type == TransactionType.BUY:
                buyers.add(tx.insider.name)
            elif tx.transaction_type == TransactionType.SELL:
                sellers.add(tx.insider.name)

        # Check if we meet the threshold
        if len(buyers) >= self.thresholds.min_insider_count:
            direction = "buying"
            insiders = buyers
            relevant_txs = [tx for tx in all_txs if tx.transaction_type == TransactionType.BUY]
        elif len(sellers) >= self.thresholds.min_insider_count:
            direction = "selling"
            insiders = sellers
            relevant_txs = [tx for tx in all_txs if tx.transaction_type == TransactionType.SELL]
        else:
            return None

        # Only alert if this transaction added a new insider
        prev_insiders = insiders - {transaction.insider.name}
        if len(prev_insiders) >= self.thresholds.min_insider_count:
            return None

        # Determine severity based on number of insiders and their roles
        if len(insiders) >= 5:
            severity = AlertSeverity.CRITICAL
        elif len(insiders) >= 3:
            severity = AlertSeverity.HIGH
        else:
            severity = AlertSeverity.MEDIUM

        total_value = sum(tx.total_value_nok for tx in relevant_txs)
        insider_list = ", ".join(sorted(insiders)[:5])
        if len(insiders) > 5:
            insider_list += f" and {len(insiders) - 5} more"

        return Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.INSIDER_CLUSTER,
            severity=severity,
            company=transaction.company,
            transactions=relevant_txs,
            title=f"Multiple Insiders {direction.title()}: {transaction.company.ticker}",
            summary=(
                f"{len(insiders)} insiders are {direction} {transaction.company.name}: "
                f"{insider_list}. "
                f"Total value: {total_value:,.0f} NOK over {self.thresholds.aggregate_window_days} days"
            ),
            metrics={
                "insider_count": len(insiders),
                "threshold_count": self.thresholds.min_insider_count,
                "total_value_nok": float(total_value),
                "insiders": list(insiders),
            },
        )


class DirectionChangeRule(AlertRule):
    """Alert when an insider reverses their trading direction."""

    name = "direction_change"

    def evaluate(
        self,
        transaction: InsiderTransaction,
        historical_transactions: list[InsiderTransaction],
    ) -> Optional[Alert]:
        # Look for previous transactions by the same insider in the same company
        cutoff = datetime.now() - timedelta(days=90)  # Look back 90 days

        prev_txs = [
            tx for tx in historical_transactions
            if tx.company.ticker == transaction.company.ticker
            and tx.insider.name == transaction.insider.name
            and tx.transaction_date >= cutoff
            and tx.transaction_type in (TransactionType.BUY, TransactionType.SELL)
        ]

        if not prev_txs:
            return None

        # Get the most recent previous transaction
        prev_txs.sort(key=lambda x: x.transaction_date, reverse=True)
        most_recent = prev_txs[0]

        # Check if direction changed
        current_is_buy = transaction.transaction_type == TransactionType.BUY
        prev_is_buy = most_recent.transaction_type == TransactionType.BUY

        if current_is_buy == prev_is_buy:
            return None

        # Direction changed!
        new_direction = "buying" if current_is_buy else "selling"
        old_direction = "selling" if current_is_buy else "buying"

        # Higher severity if the previous position was significant
        days_since = (transaction.transaction_date - most_recent.transaction_date).days

        if days_since <= 30 and most_recent.total_value_nok >= 1_000_000:
            severity = AlertSeverity.HIGH
        elif days_since <= 30:
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW

        return Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.DIRECTION_CHANGE,
            severity=severity,
            company=transaction.company,
            transactions=[transaction, most_recent],
            title=f"Insider Direction Change: {transaction.company.ticker}",
            summary=(
                f"{transaction.insider.name} switched from {old_direction} to {new_direction} "
                f"{transaction.company.name}. Previous: {old_direction} {most_recent.shares:,} shares "
                f"({most_recent.total_value_nok:,.0f} NOK) on {most_recent.transaction_date.strftime('%Y-%m-%d')}. "
                f"Now: {new_direction} {transaction.shares:,} shares ({transaction.total_value_nok:,.0f} NOK)"
            ),
            metrics={
                "days_since_previous": days_since,
                "previous_direction": old_direction,
                "current_direction": new_direction,
                "previous_value_nok": float(most_recent.total_value_nok),
                "current_value_nok": float(transaction.total_value_nok),
            },
        )


class AlertRulesEngine:
    """Engine that evaluates all alert rules against transactions."""

    def __init__(self, thresholds: Optional[AlertThresholds] = None):
        self.thresholds = thresholds or AlertThresholds()
        self.rules: list[AlertRule] = [
            LargeSingleTransactionRule(self.thresholds),
            HighPercentageTradeRule(self.thresholds),
            AggregateActivityRule(self.thresholds),
            InsiderClusterRule(self.thresholds),
            DirectionChangeRule(self.thresholds),
        ]
        self._historical_transactions: list[InsiderTransaction] = []
        self._alerted_transaction_ids: set[str] = set()

    def add_historical_transactions(self, transactions: list[InsiderTransaction]) -> None:
        """Add historical transactions for context.

        Args:
            transactions: List of historical transactions
        """
        self._historical_transactions.extend(transactions)

        # Deduplicate by ID
        seen = set()
        unique = []
        for tx in self._historical_transactions:
            if tx.id not in seen:
                seen.add(tx.id)
                unique.append(tx)
        self._historical_transactions = unique

        # Sort by date
        self._historical_transactions.sort(key=lambda x: x.transaction_date)

    def evaluate_transaction(self, transaction: InsiderTransaction) -> list[Alert]:
        """Evaluate a transaction against all rules.

        Args:
            transaction: The transaction to evaluate

        Returns:
            List of triggered alerts
        """
        # Skip if we've already processed this transaction
        if transaction.id in self._alerted_transaction_ids:
            return []

        alerts = []

        for rule in self.rules:
            try:
                alert = rule.evaluate(transaction, self._historical_transactions)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                print(f"Error evaluating rule {rule.name}: {e}")
                continue

        # Mark transaction as processed
        self._alerted_transaction_ids.add(transaction.id)

        # Add to historical transactions for future context
        if transaction not in self._historical_transactions:
            self._historical_transactions.append(transaction)

        return alerts

    def evaluate_transactions(self, transactions: list[InsiderTransaction]) -> list[Alert]:
        """Evaluate multiple transactions against all rules.

        Args:
            transactions: List of transactions to evaluate

        Returns:
            List of all triggered alerts
        """
        all_alerts = []

        # Sort by date to process in chronological order
        sorted_txs = sorted(transactions, key=lambda x: x.transaction_date)

        for transaction in sorted_txs:
            alerts = self.evaluate_transaction(transaction)
            all_alerts.extend(alerts)

        return all_alerts

    def get_summary_stats(self) -> dict:
        """Get summary statistics about processed transactions.

        Returns:
            Dictionary with summary statistics
        """
        # Group by company
        by_company: dict[str, list[InsiderTransaction]] = defaultdict(list)
        for tx in self._historical_transactions:
            by_company[tx.company.ticker].append(tx)

        # Calculate stats
        total_buy_value = sum(
            tx.total_value_nok for tx in self._historical_transactions
            if tx.transaction_type == TransactionType.BUY
        )
        total_sell_value = sum(
            tx.total_value_nok for tx in self._historical_transactions
            if tx.transaction_type == TransactionType.SELL
        )

        return {
            "total_transactions": len(self._historical_transactions),
            "unique_companies": len(by_company),
            "unique_insiders": len(set(tx.insider.name for tx in self._historical_transactions)),
            "total_buy_value_nok": float(total_buy_value),
            "total_sell_value_nok": float(total_sell_value),
            "alerted_transactions": len(self._alerted_transaction_ids),
        }

    def clear_history(self) -> None:
        """Clear all historical data."""
        self._historical_transactions.clear()
        self._alerted_transaction_ids.clear()
