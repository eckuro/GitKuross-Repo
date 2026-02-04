"""Data models for insider trading alerts."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Type of insider transaction."""

    BUY = "buy"
    SELL = "sell"
    GIFT = "gift"
    EXERCISE_OPTIONS = "exercise_options"
    OTHER = "other"


class InsiderRole(str, Enum):
    """Role of the insider in the company."""

    CEO = "ceo"
    CFO = "cfo"
    BOARD_MEMBER = "board_member"
    BOARD_CHAIR = "board_chair"
    PRIMARY_INSIDER = "primary_insider"
    RELATED_PARTY = "related_party"
    OTHER = "other"


class CompanySize(str, Enum):
    """Company size classification by market cap."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    UNKNOWN = "unknown"


class Company(BaseModel):
    """Company information."""

    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company name")
    isin: str = Field(default="", description="ISIN code")
    market_cap_nok: Optional[Decimal] = Field(
        default=None, description="Market capitalization in NOK"
    )
    shares_outstanding: Optional[int] = Field(
        default=None, description="Total shares outstanding"
    )
    size_classification: CompanySize = Field(
        default=CompanySize.UNKNOWN, description="Size classification"
    )
    sector: str = Field(default="", description="Industry sector")

    def __hash__(self) -> int:
        return hash(self.ticker)


class Insider(BaseModel):
    """Insider information."""

    name: str = Field(description="Name of the insider")
    role: InsiderRole = Field(default=InsiderRole.OTHER, description="Role in company")
    role_description: str = Field(default="", description="Detailed role description")

    def __hash__(self) -> int:
        return hash((self.name, self.role))


class InsiderTransaction(BaseModel):
    """A single insider trading transaction."""

    id: str = Field(description="Unique transaction ID")
    company: Company = Field(description="Company involved")
    insider: Insider = Field(description="Insider who made the transaction")
    transaction_type: TransactionType = Field(description="Type of transaction")
    transaction_date: datetime = Field(description="Date of transaction")
    publication_date: datetime = Field(description="Date published to market")
    shares: int = Field(description="Number of shares")
    price_per_share_nok: Decimal = Field(description="Price per share in NOK")
    total_value_nok: Decimal = Field(description="Total transaction value in NOK")
    shares_after_transaction: Optional[int] = Field(
        default=None, description="Insider's holding after transaction"
    )
    source_url: str = Field(default="", description="URL to original announcement")
    raw_data: dict = Field(default_factory=dict, description="Raw data from source")

    @property
    def shares_percent(self) -> Optional[float]:
        """Calculate transaction as percentage of outstanding shares."""
        if self.company.shares_outstanding:
            return (self.shares / self.company.shares_outstanding) * 100
        return None


class AlertType(str, Enum):
    """Types of alerts that can be triggered."""

    LARGE_SINGLE_TRANSACTION = "large_single_transaction"
    HIGH_PERCENTAGE_TRADE = "high_percentage_trade"
    AGGREGATE_ACTIVITY = "aggregate_activity"
    INSIDER_CLUSTER = "insider_cluster"
    DIRECTION_CHANGE = "direction_change"


class AlertSeverity(str, Enum):
    """Severity level of an alert."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(BaseModel):
    """An alert triggered by insider trading activity."""

    id: str = Field(description="Unique alert ID")
    alert_type: AlertType = Field(description="Type of alert")
    severity: AlertSeverity = Field(description="Severity level")
    company: Company = Field(description="Company involved")
    transactions: list[InsiderTransaction] = Field(description="Related transactions")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    title: str = Field(description="Alert title")
    summary: str = Field(description="Human-readable summary")
    metrics: dict = Field(default_factory=dict, description="Relevant metrics")

    def format_console(self) -> str:
        """Format alert for console output."""
        severity_colors = {
            AlertSeverity.LOW: "green",
            AlertSeverity.MEDIUM: "yellow",
            AlertSeverity.HIGH: "red",
            AlertSeverity.CRITICAL: "bold red",
        }
        color = severity_colors.get(self.severity, "white")

        lines = [
            f"[{color}]{'=' * 60}[/{color}]",
            f"[{color}][{self.severity.value.upper()}] {self.title}[/{color}]",
            f"Company: {self.company.name} ({self.company.ticker})",
            f"Type: {self.alert_type.value}",
            f"Time: {self.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            self.summary,
            "",
        ]

        if self.transactions:
            lines.append("Transactions:")
            for tx in self.transactions[:5]:  # Show max 5 transactions
                direction = "BUY" if tx.transaction_type == TransactionType.BUY else "SELL"
                lines.append(
                    f"  - {tx.insider.name}: {direction} {tx.shares:,} shares @ "
                    f"{tx.price_per_share_nok:.2f} NOK = {tx.total_value_nok:,.0f} NOK"
                )

        lines.append(f"[{color}]{'=' * 60}[/{color}]")
        return "\n".join(lines)

    def format_slack(self) -> dict:
        """Format alert for Slack webhook."""
        severity_emoji = {
            AlertSeverity.LOW: ":large_green_circle:",
            AlertSeverity.MEDIUM: ":large_yellow_circle:",
            AlertSeverity.HIGH: ":red_circle:",
            AlertSeverity.CRITICAL: ":rotating_light:",
        }
        emoji = severity_emoji.get(self.severity, ":bell:")

        tx_lines = []
        for tx in self.transactions[:5]:
            direction = ":chart_with_upwards_trend:" if tx.transaction_type == TransactionType.BUY else ":chart_with_downwards_trend:"
            tx_lines.append(
                f"{direction} {tx.insider.name} ({tx.insider.role.value}): "
                f"{tx.shares:,} shares @ {tx.price_per_share_nok:.2f} NOK"
            )

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {self.title}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Company:*\n{self.company.name} ({self.company.ticker})"},
                        {"type": "mrkdwn", "text": f"*Severity:*\n{self.severity.value.upper()}"},
                        {"type": "mrkdwn", "text": f"*Type:*\n{self.alert_type.value}"},
                        {"type": "mrkdwn", "text": f"*Time:*\n{self.triggered_at.strftime('%Y-%m-%d %H:%M')}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": self.summary},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Transactions:*\n" + "\n".join(tx_lines)},
                },
            ],
        }
