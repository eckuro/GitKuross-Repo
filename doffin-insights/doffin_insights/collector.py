"""Orchestrates fetch → parse → store for all vendor keywords."""
from __future__ import annotations

from datetime import date
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .database import Database
from .fetcher import DoffinClient
from .models import VENDOR_KEYWORDS, Vendor
from .parser import parse_notice

console = Console()

# Years with reliable Doffin API coverage
DEFAULT_FETCH_FROM = date(2016, 1, 1)


def collect(
    db: Database,
    date_from: date = DEFAULT_FETCH_FROM,
    date_to: Optional[date] = None,
    vendors: Optional[list[Vendor]] = None,
    dry_run: bool = False,
) -> dict[str, int]:
    date_to = date_to or date.today()
    target_vendors = vendors or list(Vendor)
    stats: dict[str, int] = {}

    # Build a flat list of (vendor, keyword) pairs to fetch
    search_terms: list[tuple[Vendor, str]] = []
    for vendor in target_vendors:
        for kw in VENDOR_KEYWORDS[vendor]:
            search_terms.append((vendor, kw))

    console.print(
        f"\n[bold]Collecting Doffin notices[/] "
        f"[dim]{date_from} → {date_to}[/] "
        f"— {len(search_terms)} search terms across {len(target_vendors)} vendors\n"
    )

    seen_ids: set[str] = set()
    total_saved = 0

    with DoffinClient() as client:
        for vendor, keyword in search_terms:
            console.print(f"[cyan]→[/] [{vendor.value}] searching [bold]'{keyword}'[/]")

            if dry_run:
                console.print("  [dim](dry run — skipping)[/]")
                continue

            raw_items = client.search_all_pages(
                query=keyword,
                date_from=date_from,
                date_to=date_to,
            )

            notices = []
            for raw in raw_items:
                notice = parse_notice(raw)
                if notice is None or notice.notice_id in seen_ids:
                    continue
                seen_ids.add(notice.notice_id)
                # Ensure the vendor we searched for is in matched list even if
                # keyword matching on stored text misses abbreviations.
                if vendor.value not in notice.matched_vendors:
                    notice.matched_vendors.append(vendor.value)
                notices.append(notice)

            saved = db.upsert_many(notices)
            total_saved += saved
            stats[vendor.value] = stats.get(vendor.value, 0) + saved
            console.print(f"  [green]✓[/] {saved} new notices stored")

    console.print(
        f"\n[bold green]Done.[/] {total_saved} notices stored "
        f"({db.count_with_vendor_match()} total with vendor matches)\n"
    )
    return stats
