"""
HTTP clients for two data sources:

  DoffinClient  — Norway's national procurement register (doffin.no)
                  REST API at https://doffin.no/api/2.0
                  Status: endpoint unconfirmed; probed at runtime.

  TEDClient     — EU Tenders Electronic Daily open-data API (ted.europa.eu)
                  Covers all Norwegian notices above EU threshold (~1.3M NOK).
                  Free API key from https://developer.ted.europa.eu
                  Set env var TED_API_KEY or pass api_key= to constructor.
                  Docs: https://ted.europa.eu/api/swagger-ui/index.html

The collector tries Doffin first; if it returns a non-200 or connection error
it automatically falls back to TED for that search term.
"""
from __future__ import annotations

import os
import time
from datetime import date
from typing import Any, Optional

import httpx
from rich.console import Console

console = Console(stderr=True)

REQUEST_DELAY = 0.5   # seconds between requests — be polite to both APIs
DOFFIN_BASE   = "https://doffin.no/api/2.0"
TED_BASE      = "https://ted.europa.eu/api/v3.0"
TED_PAGE_SIZE = 100   # TED supports up to 100 per page


# ── Shared helpers ────────────────────────────────────────────────────────────

def _make_client(timeout: float = 30.0) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        headers={
            "Accept": "application/json",
            "User-Agent": "doffin-insights/0.1 (research; github.com/eckuro/gitkuross-repo)",
        },
        follow_redirects=True,
    )


class _BaseClient:
    def __init__(self, timeout: float = 30.0):
        self._http = _make_client(timeout)
        self._last_request: float = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request = time.monotonic()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "_BaseClient":
        return self  # type: ignore[return-value]

    def __exit__(self, *_: Any) -> None:
        self.close()


# ── Doffin ────────────────────────────────────────────────────────────────────

class DoffinClient(_BaseClient):
    """Client for doffin.no REST API."""

    def __init__(self, base_url: str = DOFFIN_BASE, timeout: float = 30.0):
        super().__init__(timeout)
        self.base_url = base_url.rstrip("/")

    def probe(self) -> bool:
        """Return True if the Doffin API endpoint is reachable."""
        try:
            self._throttle()
            resp = self._http.get(
                f"{self.base_url}/Notices",
                params={"search": "test", "pageSize": 1},
            )
            return resp.status_code < 500
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def search_all_pages(
        self,
        query: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        max_pages: int = 200,
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        page_size = 50

        for page in range(1, max_pages + 1):
            self._throttle()
            params: dict[str, Any] = {
                "search": query,
                "page": page,
                "pageSize": page_size,
            }
            if date_from:
                params["publishedFrom"] = date_from.isoformat()
            if date_to:
                params["publishedTo"] = date_to.isoformat()

            try:
                resp = self._http.get(f"{self.base_url}/Notices", params=params)
                resp.raise_for_status()
                result = resp.json()
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
                console.print(f"    [yellow]Doffin error page {page}: {exc}[/]")
                break

            items = result.get("items") or result.get("data") or result.get("results") or []
            if not items:
                break

            all_items.extend(items)
            total = result.get("total") or result.get("totalCount") or 0
            console.print(
                f"    [dim]doffin '{query}' p{page}: {len(items)} "
                f"(total {len(all_items)}/{total})[/]"
            )

            if total and len(all_items) >= total:
                break
            if len(items) < page_size:
                break

        return all_items


# ── TED ───────────────────────────────────────────────────────────────────────

# TED eForms notice-type codes we care about
TED_NOTICE_TYPES = [
    "cn-standard",      # Contract notice (standard)
    "can-standard",     # Contract award notice (standard)
    "cn-defen",         # Defence contract notice
    "can-defen",        # Defence award
    "pin-buyer",        # Prior information notice
]


class TEDClient(_BaseClient):
    """
    Client for the TED (Tenders Electronic Daily) v3 API.

    Requires a free API key from https://developer.ted.europa.eu
    Pass via TED_API_KEY env var or the api_key constructor argument.

    Uses POST /notices/search with a QL query string.
    Norway filter: ND ~ NO (buyer country = Norway).
    Docs: https://ted.europa.eu/api/swagger-ui/index.html
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 60.0):
        super().__init__(timeout)
        self.base_url = TED_BASE
        self.api_key = api_key or os.environ.get("TED_API_KEY", "")
        if self.api_key:
            self._http.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _build_query(
        self,
        keyword: str,
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> str:
        parts = [
            f'ND ~ NO',                           # Norway only
            f'TD ~ ({" OR ".join(TED_NOTICE_TYPES)})',
        ]
        # Keyword search across title + description fields
        parts.append(f'(TI ~ "{keyword}" OR DS ~ "{keyword}")')

        if date_from:
            parts.append(f'PD >= {date_from.strftime("%Y%m%d")}')
        if date_to:
            parts.append(f'PD <= {date_to.strftime("%Y%m%d")}')

        return " AND ".join(parts)

    def search_all_pages(
        self,
        query: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        max_pages: int = 200,
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        page = 1

        while page <= max_pages:
            self._throttle()
            payload = {
                "query": self._build_query(query, date_from, date_to),
                "page": page,
                "pageSize": TED_PAGE_SIZE,
                "fields": [
                    "ND",   # notice number
                    "TI",   # title
                    "DS",   # short description
                    "ND",   # dossier number
                    "CA",   # contracting authority
                    "TD",   # notice type
                    "PD",   # publication date
                    "DL",   # deadline
                    "VA",   # estimated value
                    "PC",   # CPV codes
                    "AU",   # award info
                ],
            }

            try:
                resp = self._http.post(
                    f"{self.base_url}/notices/search",
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
                console.print(f"    [yellow]TED error page {page}: {exc}[/]")
                break

            notices = result.get("notices") or result.get("results") or result.get("items") or []
            if not notices:
                break

            all_items.extend(notices)
            total = result.get("total") or result.get("totalNotices") or 0
            console.print(
                f"    [dim]ted '{query}' p{page}: {len(notices)} "
                f"(total {len(all_items)}/{total})[/]"
            )

            if total and len(all_items) >= total:
                break
            if len(notices) < TED_PAGE_SIZE:
                break

            page += 1

        return all_items


# ── Auto-selecting facade ──────────────────────────────────────────────────────

class SmartClient:
    """
    Tries Doffin first. If Doffin is unreachable or returns no results,
    falls back to TED automatically.

    Use as a context manager — closes both underlying HTTP clients on exit.
    """

    def __init__(self, ted_api_key: Optional[str] = None):
        self._doffin = DoffinClient()
        self._ted = TEDClient(api_key=ted_api_key)
        self._doffin_ok: Optional[bool] = None  # None = not yet probed

    def _doffin_available(self) -> bool:
        if self._doffin_ok is None:
            console.print("  [dim]Probing Doffin API…[/]", end=" ")
            self._doffin_ok = self._doffin.probe()
            status = "[green]✓ reachable[/]" if self._doffin_ok else "[yellow]unreachable — using TED[/]"
            console.print(status)
        return self._doffin_ok

    def search_all_pages(
        self,
        query: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        source: str = "auto",  # "auto" | "doffin" | "ted"
    ) -> tuple[list[dict[str, Any]], str]:
        """
        Returns (items, source_used) where source_used is "doffin" or "ted".
        """
        use_doffin = source == "doffin" or (source == "auto" and self._doffin_available())

        if use_doffin:
            items = self._doffin.search_all_pages(query, date_from, date_to)
            if items:
                return items, "doffin"
            # Doffin returned nothing — try TED as fallback
            console.print(f"    [dim]Doffin returned 0 results, trying TED…[/]")

        items = self._ted.search_all_pages(query, date_from, date_to)
        return items, "ted"

    def close(self) -> None:
        self._doffin.close()
        self._ted.close()

    def __enter__(self) -> "SmartClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
