"""Configuration management for Oslo Insider Alerts."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AlertThresholds(BaseSettings):
    """Thresholds for triggering alerts on insider trading activity."""

    model_config = SettingsConfigDict(env_prefix="ALERT_")

    # Minimum transaction value (NOK) to consider as "heavy"
    min_transaction_value_nok: int = Field(
        default=500_000,
        description="Minimum single transaction value in NOK to trigger alert",
    )

    # Minimum shares as percentage of total outstanding
    min_shares_percent: float = Field(
        default=0.1,
        description="Minimum percentage of outstanding shares in single transaction",
    )

    # Aggregate threshold - total insider activity within time window
    aggregate_value_nok: int = Field(
        default=2_000_000,
        description="Aggregate insider transaction value in NOK within time window",
    )

    aggregate_window_days: int = Field(
        default=7,
        description="Time window in days for aggregate calculations",
    )

    # Multiple insiders buying/selling threshold
    min_insider_count: int = Field(
        default=2,
        description="Minimum number of insiders trading in same direction to trigger cluster alert",
    )


class CompanySizeFilter(BaseSettings):
    """Configuration for filtering companies by market cap."""

    model_config = SettingsConfigDict(env_prefix="COMPANY_")

    # Market cap thresholds in NOK (billions)
    small_cap_max_nok_billions: float = Field(
        default=5.0,
        description="Maximum market cap for small-cap classification (NOK billions)",
    )

    medium_cap_max_nok_billions: float = Field(
        default=25.0,
        description="Maximum market cap for medium-cap classification (NOK billions)",
    )

    # Option to include specific company tickers regardless of size
    include_tickers: list[str] = Field(
        default_factory=list,
        description="Always include these tickers regardless of market cap",
    )

    # Option to exclude specific company tickers
    exclude_tickers: list[str] = Field(
        default_factory=list,
        description="Always exclude these tickers from alerts",
    )


class NotificationSettings(BaseSettings):
    """Settings for alert notifications."""

    model_config = SettingsConfigDict(env_prefix="NOTIFY_")

    # Notification channels to use
    channels: list[Literal["console", "email", "slack"]] = Field(
        default=["console"],
        description="Notification channels to use for alerts",
    )

    # Email settings
    email_smtp_host: str = Field(default="", description="SMTP server hostname")
    email_smtp_port: int = Field(default=587, description="SMTP server port")
    email_smtp_user: str = Field(default="", description="SMTP username")
    email_smtp_password: str = Field(default="", description="SMTP password")
    email_from: str = Field(default="", description="From email address")
    email_to: list[str] = Field(default_factory=list, description="Recipient email addresses")

    # Slack settings
    slack_webhook_url: str = Field(default="", description="Slack incoming webhook URL")
    slack_channel: str = Field(default="#insider-alerts", description="Slack channel name")


class DataSourceSettings(BaseSettings):
    """Settings for data sources."""

    model_config = SettingsConfigDict(env_prefix="DATA_")

    # Oslo Bors NewsWeb URL
    newsweb_base_url: str = Field(
        default="https://newsweb.oslobors.no",
        description="Base URL for Oslo Bors NewsWeb",
    )

    # Rate limiting
    request_delay_seconds: float = Field(
        default=1.0,
        description="Delay between API requests in seconds",
    )

    # Cache settings
    cache_ttl_minutes: int = Field(
        default=15,
        description="Cache TTL for market data in minutes",
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Database path
    database_url: str = Field(
        default="sqlite+aiosqlite:///oslo_insider_alerts.db",
        description="Database connection URL",
    )

    # Polling interval
    poll_interval_minutes: int = Field(
        default=30,
        description="How often to check for new insider trades (minutes)",
    )

    # Sub-configurations
    thresholds: AlertThresholds = Field(default_factory=AlertThresholds)
    company_filter: CompanySizeFilter = Field(default_factory=CompanySizeFilter)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    data_source: DataSourceSettings = Field(default_factory=DataSourceSettings)


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from environment and optional config file."""
    if config_path and config_path.exists():
        return Settings(_env_file=config_path)
    return Settings()
