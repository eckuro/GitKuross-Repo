"""Tests for database upsert and query logic."""
import tempfile
from datetime import date
from pathlib import Path

import pytest
from doffin_insights.database import Database
from doffin_insights.models import NoticeType, ProcurementNotice


def make_notice(notice_id: str, vendor: str, year: int = 2023) -> ProcurementNotice:
    return ProcurementNotice(
        notice_id=notice_id,
        title=f"Test notice {notice_id}",
        contracting_authority="Test kommune",
        authority_type="Kommune",
        notice_type=NoticeType.CONTRACT,
        published_date=date(year, 6, 1),
        estimated_value_nok=1_000_000.0,
        matched_vendors=[vendor],
    )


def test_upsert_and_count():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    with Database(db_path) as db:
        db.upsert_many([
            make_notice("1", "SAP"),
            make_notice("2", "Microsoft Dynamics"),
        ])
        assert db.count() == 2
        assert db.count_with_vendor_match() == 2


def test_upsert_deduplicates():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    with Database(db_path) as db:
        notice = make_notice("dupe", "SAP")
        db.upsert_many([notice, notice])
        assert db.count() == 1


def test_all_matched_returns_only_matched():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    with Database(db_path) as db:
        matched = make_notice("m1", "Oracle")
        unmatched = ProcurementNotice(notice_id="u1", title="No vendor here")
        db.upsert_many([matched, unmatched])
        results = db.all_matched()
        assert len(results) == 1
        assert results[0]["notice_id"] == "m1"
