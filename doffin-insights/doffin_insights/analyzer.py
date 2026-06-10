"""Aggregate and compute statistics from stored notices."""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from .database import Database
from .models import NoticeType, VendorStats


def _explode_vendors(rows: list[dict]) -> list[dict]:
    """Expand rows with multiple vendors into one row per vendor."""
    out = []
    for row in rows:
        vendors = json.loads(row["matched_vendors"])
        for v in vendors:
            out.append({**row, "_vendor": v})
    return out


def compute_vendor_stats(db: Database) -> dict[str, VendorStats]:
    rows = db.all_matched()
    exploded = _explode_vendors(rows)

    by_vendor: dict[str, list[dict]] = defaultdict(list)
    for row in exploded:
        by_vendor[row["_vendor"]].append(row)

    stats: dict[str, VendorStats] = {}
    for vendor, vendor_rows in by_vendor.items():
        by_year: dict[int, int] = defaultdict(int)
        by_auth: dict[str, int] = defaultdict(int)
        auth_counts: dict[str, int] = defaultdict(int)
        total_value = 0.0
        award_count = 0
        value_count = 0

        for row in vendor_rows:
            year_str = (row.get("published_date") or "")[:4]
            if year_str.isdigit():
                by_year[int(year_str)] += 1

            auth_type = row.get("authority_type") or "Ukjent"
            by_auth[auth_type] += 1

            auth_name = row.get("contracting_authority") or "Ukjent"
            auth_counts[auth_name] += 1

            if row.get("notice_type") == NoticeType.AWARD.value:
                award_count += 1

            val = row.get("estimated_value_nok")
            if val:
                total_value += float(val)
                value_count += 1

        top_auth = sorted(auth_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        avg_val = total_value / value_count if value_count else 0.0

        stats[vendor] = VendorStats(
            vendor=vendor,
            total_notices=len(vendor_rows),
            award_notices=award_count,
            total_value_nok=total_value,
            avg_value_nok=avg_val,
            by_year=dict(by_year),
            by_authority_type=dict(by_auth),
            top_authorities=top_auth,
        )

    return stats


def yearly_comparison(db: Database) -> dict[int, dict[str, int]]:
    """Return {year: {vendor: count}} for charting multi-vendor trends."""
    rows = db.all_matched()
    exploded = _explode_vendors(rows)

    result: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in exploded:
        year_str = (row.get("published_date") or "")[:4]
        if year_str.isdigit():
            result[int(year_str)][row["_vendor"]] += 1

    return {yr: dict(vendors) for yr, vendors in sorted(result.items())}


def authority_type_breakdown(db: Database) -> dict[str, dict[str, int]]:
    """Return {vendor: {authority_type: count}}."""
    rows = db.all_matched()
    exploded = _explode_vendors(rows)

    result: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in exploded:
        result[row["_vendor"]][row.get("authority_type") or "Ukjent"] += 1

    return {v: dict(auth) for v, auth in result.items()}
