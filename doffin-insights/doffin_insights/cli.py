"""CLI entry point for doffin-insights."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import os

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Analyse Norwegian public procurement (Doffin) for enterprise software demand")
console = Console()

DEFAULT_DB = Path("doffin_insights.db")
DEFAULT_OUT = Path("output/charts")


@app.command()
def collect(
    db_path: Path = typer.Option(DEFAULT_DB, "--db", help="SQLite database path"),
    date_from: str = typer.Option("2016-01-01", "--from", help="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = typer.Option(None, "--to", help="End date (YYYY-MM-DD)"),
    source: str = typer.Option(
        "auto",
        "--source",
        help="Data source: 'auto' (Doffin with TED fallback), 'doffin', or 'ted'",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print search plan without fetching"),
) -> None:
    """Fetch notices for all tracked enterprise software vendors.

    Source selection:

    \b
      auto   — tries Doffin first; falls back to TED if unreachable (default)
      doffin — Doffin only (Norway's national register, all contract sizes)
      ted    — TED only (EU open data, guaranteed free, above-threshold only)
    """
    from .collector import collect as do_collect
    from .database import Database

    if source not in ("auto", "doffin", "ted"):
        console.print(f"[red]Unknown source '{source}'. Use auto, doffin, or ted.[/]")
        raise typer.Exit(1)

    from_date = date.fromisoformat(date_from)
    to_date = date.fromisoformat(date_to) if date_to else date.today()

    with Database(db_path) as db:
        do_collect(db, date_from=from_date, date_to=to_date, source=source, dry_run=dry_run)  # type: ignore[arg-type]
        console.print(f"[dim]Database: {db_path} ({db.count()} total rows)[/]")


@app.command()
def analyse(
    db_path: Path = typer.Option(DEFAULT_DB, "--db"),
) -> None:
    """Print a statistics summary table to the console."""
    from .analyzer import compute_vendor_stats
    from .database import Database

    with Database(db_path) as db:
        stats = compute_vendor_stats(db)

    if not stats:
        console.print("[yellow]No vendor-matched notices in database. Run 'collect' first.[/]")
        raise typer.Exit(1)

    table = Table(title="Doffin Enterprise Software Demand — Norway", show_lines=True)
    table.add_column("Leverandør", style="bold")
    table.add_column("Kunngjøringer", justify="right")
    table.add_column("Herav tildeling", justify="right")
    table.add_column("Tildeling %", justify="right")
    table.add_column("Total verdi (NOK)", justify="right")
    table.add_column("Snitt verdi (NOK)", justify="right")

    for vendor_name, s in sorted(stats.items(), key=lambda x: x[1].total_notices, reverse=True):
        award_pct = (s.award_notices / s.total_notices * 100) if s.total_notices else 0
        table.add_row(
            vendor_name,
            str(s.total_notices),
            str(s.award_notices),
            f"{award_pct:.0f}%",
            f"{s.total_value_nok:,.0f}" if s.total_value_nok else "—",
            f"{s.avg_value_nok:,.0f}" if s.avg_value_nok else "—",
        )

    console.print(table)


@app.command()
def charts(
    db_path: Path = typer.Option(DEFAULT_DB, "--db"),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out", help="Output directory for chart PNGs"),
) -> None:
    """Generate all charts and save to output directory."""
    from .analyzer import compute_vendor_stats
    from .database import Database
    from .visualizer import render_all

    with Database(db_path) as db:
        stats = compute_vendor_stats(db)
        if not stats:
            console.print("[yellow]No data. Run 'collect' first.[/]")
            raise typer.Exit(1)
        generated = render_all(db, stats, out_dir)

    console.print(f"\n[bold green]{len(generated)} charts saved to {out_dir}/[/]")
    for p in generated:
        console.print(f"  [dim]{p}[/]")


@app.command()
def status(
    db_path: Path = typer.Option(DEFAULT_DB, "--db"),
) -> None:
    """Show what's currently in the database."""
    from .database import Database

    if not db_path.exists():
        console.print("[yellow]No database found. Run 'collect' first.[/]")
        raise typer.Exit(1)

    with Database(db_path) as db:
        total = db.count()
        matched = db.count_with_vendor_match()
        rows = db.vendor_yearly_counts()

    from collections import Counter
    import json

    vendor_counts: Counter = Counter()
    for row in rows:
        for v in json.loads(row["matched_vendors"]):
            vendor_counts[v] += 1

    console.print(f"\n[bold]Database:[/] {db_path}")
    console.print(f"  Total rows:          {total}")
    console.print(f"  With vendor matches: {matched}\n")

    table = Table(title="Matches per leverandør")
    table.add_column("Leverandør", style="bold")
    table.add_column("Kunngjøringer", justify="right")
    for vendor, count in vendor_counts.most_common():
        table.add_row(vendor, str(count))
    console.print(table)


@app.command()
def check() -> None:
    """Check connectivity to Doffin and TED before running a full collect."""
    import httpx

    results = []

    for label, url, method, payload in [
        (
            "Doffin API",
            "https://doffin.no/api/2.0/Notices?search=SAP&pageSize=1",
            "GET", None,
        ),
        (
            "TED API (no key)",
            "https://ted.europa.eu/api/v3.0/notices/search",
            "POST", {"query": "ND ~ NO AND TI ~ \"SAP\"", "page": 1, "pageSize": 1},
        ),
    ]:
        try:
            with httpx.Client(timeout=10, follow_redirects=True) as c:
                if method == "POST":
                    r = c.post(url, json=payload, headers={"Accept": "application/json"})
                else:
                    r = c.get(url, headers={"Accept": "application/json"})

            if r.status_code == 200:
                console.print(f"[green]✓[/] {label}: [bold]reachable[/] (HTTP 200)")
            elif r.status_code == 403:
                console.print(
                    f"[yellow]✗[/] {label}: [bold]403 Forbidden[/] — "
                    "likely IP block (cloud/VPN). Run locally or set TED_API_KEY."
                )
            elif r.status_code == 401:
                console.print(
                    f"[yellow]✗[/] {label}: [bold]401 Unauthorized[/] — "
                    "API key required. Set TED_API_KEY env var."
                )
            else:
                console.print(f"[yellow]?[/] {label}: HTTP {r.status_code}")
            results.append(r.status_code)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            console.print(f"[red]✗[/] {label}: connection failed — {exc}")
            results.append(0)

    ted_key = os.environ.get("TED_API_KEY", "")
    if ted_key:
        console.print(f"\n[dim]TED_API_KEY is set ({ted_key[:8]}…)[/]")
    else:
        console.print(
            "\n[dim]TED_API_KEY not set. "
            "Register free at https://developer.ted.europa.eu then:[/]\n"
            "[dim]  export TED_API_KEY=your_key_here[/]\n"
            "[dim]  doffin-insights collect --source ted[/]"
        )


if __name__ == "__main__":
    app()
