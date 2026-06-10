"""
Doffin API client.

Doffin (Database for offentlige innkjøp) is Norway's official public
procurement register. Public notices are accessible via their REST API.
API docs: https://doffin.no/api/swagger
Base: https://doffin.no/api/2.0
"""
from __future__ import annotations

import asyncio
import time
from datetime import date
from typing import Any, Optional
from urllib.parse import urlencode

import httpx
from rich.console import Console

console = Console(stderr=True)

DOFFIN_BASE = "https://doffin.no/api/2.0"
DEFAULT_PAGE_SIZE = 50
REQUEST_DELAY = 0.4  # seconds between requests — be polite


class DoffinClient:
    def __init__(self, base_url: str = DOFFIN_BASE, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "doffin-insights/0.1 (research; github.com/eckuro/gitkuross-repo)",
            },
            follow_redirects=True,
        )
        self._last_request: float = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request = time.monotonic()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._throttle()
        url = f"{self.base_url}{path}"
        resp = self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def search_notices(
        self,
        query: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        notice_type: Optional[str] = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "search": query,
            "page": page,
            "pageSize": page_size,
        }
        if date_from:
            params["publishedFrom"] = date_from.isoformat()
        if date_to:
            params["publishedTo"] = date_to.isoformat()
        if notice_type:
            params["noticeType"] = notice_type

        return self._get("/Notices", params=params)

    def get_notice(self, notice_id: str) -> dict[str, Any]:
        return self._get(f"/Notices/{notice_id}")

    def search_all_pages(
        self,
        query: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        notice_type: Optional[str] = None,
        max_pages: int = 200,
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        page = 1

        while page <= max_pages:
            try:
                result = self.search_notices(
                    query=query,
                    date_from=date_from,
                    date_to=date_to,
                    notice_type=notice_type,
                    page=page,
                )
            except httpx.HTTPStatusError as exc:
                console.print(f"[yellow]HTTP {exc.response.status_code} on page {page} for '{query}' — stopping[/]")
                break

            items = result.get("items", result.get("data", result.get("results", [])))
            if not items:
                break

            all_items.extend(items)
            total = result.get("total", result.get("totalCount", result.get("count", 0)))
            console.print(
                f"  [dim]'{query}' page {page}: {len(items)} notices "
                f"(cumulative {len(all_items)}/{total})[/]"
            )

            fetched = len(all_items)
            if total and fetched >= total:
                break
            if len(items) < DEFAULT_PAGE_SIZE:
                break

            page += 1

        return all_items

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "DoffinClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
