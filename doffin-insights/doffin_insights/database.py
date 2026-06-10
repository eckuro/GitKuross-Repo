"""SQLite persistence for procurement notices."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .models import NoticeType, ProcurementNotice

DDL = """
CREATE TABLE IF NOT EXISTS notices (
    notice_id           TEXT PRIMARY KEY,
    title               TEXT,
    description         TEXT,
    contracting_authority TEXT,
    authority_type      TEXT,
    notice_type         TEXT,
    published_date      TEXT,
    deadline_date       TEXT,
    estimated_value_nok REAL,
    cpv_codes           TEXT,
    matched_vendors     TEXT,
    raw_url             TEXT,
    fetched_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_published ON notices(published_date);
CREATE INDEX IF NOT EXISTS idx_authority_type ON notices(authority_type);
"""


class Database:
    def __init__(self, path: Path | str = "doffin_insights.db"):
        self.path = Path(path)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(DDL)
        self.conn.commit()

    def upsert(self, notice: ProcurementNotice) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO notices
            (notice_id, title, description, contracting_authority, authority_type,
             notice_type, published_date, deadline_date, estimated_value_nok,
             cpv_codes, matched_vendors, raw_url, fetched_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                notice.notice_id,
                notice.title,
                notice.description,
                notice.contracting_authority,
                notice.authority_type,
                notice.notice_type.value,
                notice.published_date.isoformat() if notice.published_date else None,
                notice.deadline_date.isoformat() if notice.deadline_date else None,
                notice.estimated_value_nok,
                json.dumps(notice.cpv_codes),
                json.dumps(notice.matched_vendors),
                notice.raw_url,
                notice.fetched_at.isoformat(),
            ),
        )

    def upsert_many(self, notices: list[ProcurementNotice]) -> int:
        saved = 0
        for n in notices:
            self.upsert(n)
            saved += 1
        self.conn.commit()
        return saved

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]

    def count_with_vendor_match(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM notices WHERE matched_vendors != '[]'"
        ).fetchone()[0]

    def all_matched(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM notices WHERE matched_vendors != '[]' ORDER BY published_date"
        ).fetchall()
        return [dict(r) for r in rows]

    def vendor_yearly_counts(self) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT
                substr(published_date, 1, 4) AS year,
                matched_vendors,
                notice_type,
                estimated_value_nok,
                authority_type
            FROM notices
            WHERE matched_vendors != '[]'
              AND published_date IS NOT NULL
            ORDER BY year
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_) -> None:
        self.close()
