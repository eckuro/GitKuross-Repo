"""Command-line interface for Oslo Insider Alerts."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .app import InsiderAlertApp
from .config import load_settings

app = typer.Typer(
    name="oslo-insider",
    help="Monitor heavy insider trading on Oslo Stock Exchange for small/medium cap companies.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"oslo-insider-alerts version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Oslo Insider Alerts - Monitor heavy insider trading on Oslo Børs."""
    pass


@app.command()
def run(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (.env format)",
    ),
    days: int = typer.Option(
        7,
        "--days",
        "-d",
        help="Number of days to look back for transactions",
    ),
    continuous: bool = typer.Option(
        False,
        "--continuous",
        help="Run continuously, polling for new transactions",
    ),
) -> None:
    """Fetch insider transactions and generate alerts."""
    settings = load_settings(config)
    application = InsiderAlertApp(settings)

    async def _run() -> None:
        try:
            await application.initialize()

            if continuous:
                await application.run_continuous()
            else:
                alerts = await application.run_once(days_back=days)
                if alerts:
                    console.print(f"\n[bold green]Generated {len(alerts)} alert(s)[/bold green]")
                else:
                    console.print("\n[dim]No alerts generated[/dim]")

        finally:
            await application.shutdown()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")


@app.command()
def check(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    ticker: Optional[str] = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Check a specific company ticker",
    ),
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Number of days to look back",
    ),
) -> None:
    """Check recent insider activity for a company or the market."""
    settings = load_settings(config)
    application = InsiderAlertApp(settings)

    async def _check() -> None:
        try:
            await application.initialize()

            if application.database:
                records = await application.database.get_recent_transactions(
                    days=days,
                    company_ticker=ticker,
                )

                if not records:
                    console.print("[dim]No transactions found[/dim]")
                    return

                # Create table
                table = Table(title=f"Recent Insider Transactions (last {days} days)")
                table.add_column("Date", style="cyan")
                table.add_column("Ticker", style="green")
                table.add_column("Insider", style="white")
                table.add_column("Type", style="yellow")
                table.add_column("Shares", justify="right")
                table.add_column("Value (NOK)", justify="right", style="bold")

                for record in records[:50]:  # Show max 50
                    tx_type_color = "green" if record.transaction_type == "buy" else "red"
                    table.add_row(
                        record.transaction_date.strftime("%Y-%m-%d"),
                        record.company_ticker,
                        record.insider_name[:20],
                        f"[{tx_type_color}]{record.transaction_type.upper()}[/{tx_type_color}]",
                        f"{record.shares:,}",
                        f"{record.total_value_nok:,.0f}",
                    )

                console.print(table)

                # Summary
                total_buy = sum(r.total_value_nok for r in records if r.transaction_type == "buy")
                total_sell = sum(r.total_value_nok for r in records if r.transaction_type == "sell")

                console.print(f"\n[green]Total Buy Volume:[/green] {total_buy:,.0f} NOK")
                console.print(f"[red]Total Sell Volume:[/red] {total_sell:,.0f} NOK")

        finally:
            await application.shutdown()

    asyncio.run(_check())


@app.command()
def stats(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Show statistics about tracked insider trading activity."""
    settings = load_settings(config)
    application = InsiderAlertApp(settings)

    async def _stats() -> None:
        try:
            await application.initialize()
            app_stats = await application.get_stats()

            console.print("\n[bold]Oslo Insider Alerts Statistics[/bold]\n")

            if "database" in app_stats:
                db_stats = app_stats["database"]
                console.print(f"Transactions (30 days): {db_stats.get('recent_transactions_30d', 0)}")

            if "rules_engine" in app_stats:
                re_stats = app_stats["rules_engine"]
                console.print(f"Total Transactions Processed: {re_stats.get('total_transactions', 0)}")
                console.print(f"Unique Companies: {re_stats.get('unique_companies', 0)}")
                console.print(f"Unique Insiders: {re_stats.get('unique_insiders', 0)}")
                console.print(f"Total Buy Value: {re_stats.get('total_buy_value_nok', 0):,.0f} NOK")
                console.print(f"Total Sell Value: {re_stats.get('total_sell_value_nok', 0):,.0f} NOK")

        finally:
            await application.shutdown()

    asyncio.run(_stats())


@app.command()
def config_template() -> None:
    """Print a template configuration file."""
    template = '''# Oslo Insider Alerts Configuration
# Copy this to .env and customize as needed

# Database
DATABASE_URL=sqlite+aiosqlite:///oslo_insider_alerts.db

# Polling interval (minutes)
POLL_INTERVAL_MINUTES=30

# Alert Thresholds
ALERT_MIN_TRANSACTION_VALUE_NOK=500000
ALERT_MIN_SHARES_PERCENT=0.1
ALERT_AGGREGATE_VALUE_NOK=2000000
ALERT_AGGREGATE_WINDOW_DAYS=7
ALERT_MIN_INSIDER_COUNT=2

# Company Size Filter (NOK billions)
COMPANY_SMALL_CAP_MAX_NOK_BILLIONS=5.0
COMPANY_MEDIUM_CAP_MAX_NOK_BILLIONS=25.0
# COMPANY_INCLUDE_TICKERS=["TICK1","TICK2"]
# COMPANY_EXCLUDE_TICKERS=["TICK3"]

# Notification Channels (comma-separated: console, email, slack)
NOTIFY_CHANNELS=["console"]

# Email Settings (if using email notifications)
# NOTIFY_EMAIL_SMTP_HOST=smtp.example.com
# NOTIFY_EMAIL_SMTP_PORT=587
# NOTIFY_EMAIL_SMTP_USER=user@example.com
# NOTIFY_EMAIL_SMTP_PASSWORD=password
# NOTIFY_EMAIL_FROM=alerts@example.com
# NOTIFY_EMAIL_TO=["recipient@example.com"]

# Slack Settings (if using slack notifications)
# NOTIFY_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
# NOTIFY_SLACK_CHANNEL=#insider-alerts

# Data Source Settings
DATA_NEWSWEB_BASE_URL=https://newsweb.oslobors.no
DATA_REQUEST_DELAY_SECONDS=1.0
DATA_CACHE_TTL_MINUTES=15
'''
    console.print(template)


@app.command()
def test_alert() -> None:
    """Generate a test alert to verify notification setup."""
    from datetime import datetime
    from decimal import Decimal
    import uuid

    from .config import Settings
    from .models import (
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
    from .notifications import NotificationManager

    settings = Settings()

    # Create a test transaction
    company = Company(
        ticker="TEST",
        name="Test Company ASA",
        isin="NO0000000000",
        market_cap_nok=Decimal("1000000000"),
        shares_outstanding=10000000,
        size_classification=CompanySize.SMALL,
    )

    insider = Insider(
        name="Test Insider",
        role=InsiderRole.CEO,
        role_description="Chief Executive Officer",
    )

    transaction = InsiderTransaction(
        id=str(uuid.uuid4()),
        company=company,
        insider=insider,
        transaction_type=TransactionType.BUY,
        transaction_date=datetime.now(),
        publication_date=datetime.now(),
        shares=50000,
        price_per_share_nok=Decimal("100.50"),
        total_value_nok=Decimal("5025000"),
        source_url="https://example.com/test",
    )

    # Create a test alert
    alert = Alert(
        id=str(uuid.uuid4()),
        alert_type=AlertType.LARGE_SINGLE_TRANSACTION,
        severity=AlertSeverity.HIGH,
        company=company,
        transactions=[transaction],
        title="TEST ALERT: Large Insider Trade",
        summary=(
            "This is a test alert. "
            "Test Insider (CEO) purchased 50,000 shares of Test Company ASA for 5,025,000 NOK."
        ),
        metrics={
            "transaction_value_nok": 5025000,
            "threshold_nok": 500000,
            "ratio": 10.05,
        },
    )

    async def _send_test() -> None:
        manager = NotificationManager(settings.notifications)
        results = await manager.send_alert(alert)

        console.print("\n[bold]Test Alert Results:[/bold]")
        for channel, success in results.items():
            status = "[green]SUCCESS[/green]" if success else "[red]FAILED[/red]"
            console.print(f"  {channel}: {status}")

        await manager.close()

    asyncio.run(_send_test())


if __name__ == "__main__":
    app()
