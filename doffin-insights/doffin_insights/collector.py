"""Orchestrates fetch → parse → store for all vendor keywords."""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from rich.console import Console

from .database import Database
from .fetcher import SmartClient
from .models import VENDOR_KEYWORDS, Vendor
from .parser import parse_notice

console = Console()

DEFAULT_FETCH_FROM = date(2016, 1, 1)
Source = Literal["auto", "doffin", "ted"]


def collect(
    db: Database,
    date_from: date = DEFAULT_FETCH_FROM,
    date_to: Optional[date] = None,
    vendors: Optional[list[Vendor]] = None,
    source: Source = "auto",
    dry_run: bool = False,
) -> dict[str, int]:
    date_to = date_to or date.today()
    target_vendors = vendors or list(Vendor)

    search_terms: list[tuple[Vendor, str]] = [
        (vendor, kw)
        for vendor in target_vendors
        for kw in VENDOR_KEYWORDS[vendor]
    ]

    console.print(
        f"\n[bold]Collecting procurement notices[/] "
        f"[dim]{date_from} → {date_to}[/] "
        f"source=[cyan]{source}[/] "
        f"— {len(search_terms)} search terms across {len(target_vendors)} vendors\n"
    )

    seen_ids: set[str] = set()
    total_saved = 0
    stats: dict[str, int] = {}
    source_tally: dict[str, int] = {"doffin": 0, "ted": 0}

    with SmartClient() as client:
        for vendor, keyword in search_terms:
            console.print(f"[cyan]→[/] [{vendor.value}] [bold]'{keyword}'[/]")

            if dry_run:
                console.print("  [dim](dry run — skipping)[/]")
                continue

            raw_items, used_source = client.search_all_pages(
                query=keyword,
                date_from=date_from,
                date_to=date_to,
                source=source,
            )

            notices = []
            for raw in raw_items:
                notice = parse_notice(raw, source=used_source)
                if notice is None or notice.notice_id in seen_ids:
                    continue
                seen_ids.add(notice.notice_id)
                if vendor.value not in notice.matched_vendors:
                    notice.matched_vendors.append(vendor.value)
                notices.append(notice)

            saved = db.upsert_many(notices)
            total_saved += saved
            stats[vendor.value] = stats.get(vendor.value, 0) + saved
            source_tally[used_source] = source_tally.get(used_source, 0) + saved
            console.print(
                f"  [green]✓[/] {saved} notices via [dim]{used_source}[/]"
            )

    console.print(
        f"\n[bold green]Done.[/] {total_saved} notices stored "
        f"(doffin: {source_tally['doffin']}, ted: {source_tally['ted']}) "
        f"— {db.count_with_vendor_match()} total with vendor matches\n"
    )
    return stats
