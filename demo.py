"""Demo script to show the alert system with sample data."""

import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from random import choice, randint, uniform

from rich.console import Console

from oslo_insider_alerts.classifier import CompanySizeClassifier
from oslo_insider_alerts.config import Settings
from oslo_insider_alerts.models import (
    Company,
    CompanySize,
    Insider,
    InsiderRole,
    InsiderTransaction,
    TransactionType,
)
from oslo_insider_alerts.notifications import NotificationManager
from oslo_insider_alerts.rules import AlertRulesEngine

console = Console()

# Sample Oslo Børs small/mid-cap companies
SAMPLE_COMPANIES = [
    ("BOUV", "Bouvet ASA", 3.2, 45_000_000),
    ("CRAYON", "Crayon Group Holding ASA", 8.5, 90_000_000),
    ("PEXIP", "Pexip Holding ASA", 2.1, 110_000_000),
    ("KAHOT", "Kahoot! ASA", 4.8, 490_000_000),
    ("VOLUE", "Volue ASA", 3.5, 140_000_000),
    ("OTOVO", "Otovo ASA", 0.8, 180_000_000),
    ("AGAS", "Avance Gas Holding", 6.2, 76_000_000),
    ("CLOUD", "Cloudberry Clean Energy", 2.9, 150_000_000),
    ("ENDUR", "Endur ASA", 1.2, 85_000_000),
    ("HUNT", "Hunter Group ASA", 0.9, 95_000_000),
]

SAMPLE_INSIDERS = [
    ("Erik Hansen", InsiderRole.CEO),
    ("Maria Olsen", InsiderRole.CFO),
    ("Lars Berg", InsiderRole.BOARD_CHAIR),
    ("Anne Johansen", InsiderRole.BOARD_MEMBER),
    ("Kari Nordmann", InsiderRole.BOARD_MEMBER),
    ("Per Iversen", InsiderRole.PRIMARY_INSIDER),
    ("Ingrid Larsen", InsiderRole.CEO),
    ("Johan Pettersen", InsiderRole.CFO),
]


def generate_sample_transactions(count: int = 25) -> list[InsiderTransaction]:
    """Generate realistic sample insider transactions."""
    transactions = []

    for i in range(count):
        ticker, name, market_cap_b, shares_out = choice(SAMPLE_COMPANIES)
        insider_name, insider_role = choice(SAMPLE_INSIDERS)

        company = Company(
            ticker=ticker,
            name=name,
            market_cap_nok=Decimal(str(market_cap_b * 1_000_000_000)),
            shares_outstanding=shares_out,
            size_classification=CompanySize.SMALL if market_cap_b < 5 else CompanySize.MEDIUM,
        )

        insider = Insider(name=insider_name, role=insider_role)

        # Generate transaction details
        tx_type = choice([TransactionType.BUY, TransactionType.BUY, TransactionType.SELL])  # Bias towards buys

        # Vary the transaction size - some small, some large
        if randint(1, 10) <= 2:  # 20% chance of large transaction
            shares = randint(20_000, 100_000)
        else:
            shares = randint(1_000, 20_000)

        price = Decimal(str(round(uniform(15.0, 150.0), 2)))
        total_value = Decimal(shares) * price

        # Random date in last 7 days
        days_ago = randint(0, 6)
        hours_ago = randint(0, 23)
        tx_date = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

        transaction = InsiderTransaction(
            id=str(uuid.uuid4())[:8],
            company=company,
            insider=insider,
            transaction_type=tx_type,
            transaction_date=tx_date,
            publication_date=tx_date + timedelta(hours=randint(1, 4)),
            shares=shares,
            price_per_share_nok=price,
            total_value_nok=total_value,
            shares_after_transaction=randint(50_000, 500_000),
            source_url=f"https://newsweb.oslobors.no/message/{randint(100000, 999999)}",
        )

        transactions.append(transaction)

    return transactions


async def run_demo():
    """Run a demonstration of the alert system."""
    console.print("\n[bold blue]═══════════════════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]       Oslo Insider Alerts - Demo with Sample Data[/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════════════════[/bold blue]\n")

    # Generate sample transactions
    console.print("[cyan]Generating sample insider transactions...[/cyan]")
    transactions = generate_sample_transactions(30)

    console.print(f"[green]Generated {len(transactions)} sample transactions[/green]\n")

    # Show sample transactions
    console.print("[bold]Sample Transactions:[/bold]")
    console.print("─" * 80)
    for tx in sorted(transactions, key=lambda x: x.transaction_date, reverse=True)[:10]:
        direction = "[green]BUY [/green]" if tx.transaction_type == TransactionType.BUY else "[red]SELL[/red]"
        console.print(
            f"{tx.transaction_date.strftime('%Y-%m-%d')} │ {tx.company.ticker:6} │ "
            f"{tx.insider.name:18} │ {direction} │ "
            f"{tx.shares:>8,} shares │ {tx.total_value_nok:>12,.0f} NOK"
        )
    console.print("─" * 80)
    console.print(f"[dim]...and {len(transactions) - 10} more transactions[/dim]\n")

    # Initialize the rules engine
    settings = Settings()
    rules_engine = AlertRulesEngine(settings.thresholds)

    # Evaluate all transactions
    console.print("[cyan]Running alert rules engine...[/cyan]")
    alerts = rules_engine.evaluate_transactions(transactions)

    if not alerts:
        console.print("[yellow]No alerts triggered with current thresholds[/yellow]")
        console.print("[dim]Try lowering ALERT_MIN_TRANSACTION_VALUE_NOK in config[/dim]\n")
    else:
        console.print(f"[bold yellow]Generated {len(alerts)} alert(s)![/bold yellow]\n")

        # Send alerts through notification manager
        notification_manager = NotificationManager(settings.notifications)

        for alert in alerts:
            console.print(alert.format_console())
            console.print()

        await notification_manager.close()

    # Show summary statistics
    stats = rules_engine.get_summary_stats()
    console.print("\n[bold]Summary Statistics:[/bold]")
    console.print("─" * 40)
    console.print(f"Total Transactions:    {stats['total_transactions']}")
    console.print(f"Unique Companies:      {stats['unique_companies']}")
    console.print(f"Unique Insiders:       {stats['unique_insiders']}")
    console.print(f"Total Buy Volume:      {stats['total_buy_value_nok']:,.0f} NOK")
    console.print(f"Total Sell Volume:     {stats['total_sell_value_nok']:,.0f} NOK")
    console.print(f"Alerts Generated:      {len(alerts)}")
    console.print("─" * 40)

    # Net insider sentiment
    net = stats['total_buy_value_nok'] - stats['total_sell_value_nok']
    if net > 0:
        console.print(f"\n[bold green]Net Insider Sentiment: +{net:,.0f} NOK (BULLISH)[/bold green]")
    else:
        console.print(f"\n[bold red]Net Insider Sentiment: {net:,.0f} NOK (BEARISH)[/bold red]")


if __name__ == "__main__":
    asyncio.run(run_demo())
