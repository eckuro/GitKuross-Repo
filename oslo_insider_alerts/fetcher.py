"""Data fetcher for Oslo Børs insider trading announcements."""

import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .config import DataSourceSettings
from .models import (
    Company,
    CompanySize,
    Insider,
    InsiderRole,
    InsiderTransaction,
    TransactionType,
)


class OsloBorsDataFetcher:
    """Fetches insider trading data from Oslo Børs NewsWeb."""

    # NewsWeb category ID for insider trading notifications (PDMR/Primary Insider Notifications)
    INSIDER_CATEGORY_ID = "1-3"  # "Meldepliktig handel"

    def __init__(self, settings: Optional[DataSourceSettings] = None):
        self.settings = settings or DataSourceSettings()
        self._client: Optional[httpx.AsyncClient] = None
        self._company_cache: dict[str, Company] = {}

    async def __aenter__(self) -> "OsloBorsDataFetcher":
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "OsloInsiderAlerts/0.1 (Financial Monitoring Tool)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5,nb;q=0.3",
            },
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    async def fetch_recent_insider_transactions(
        self,
        days_back: int = 7,
        max_items: int = 100,
    ) -> list[InsiderTransaction]:
        """Fetch recent insider trading announcements from NewsWeb.

        Args:
            days_back: Number of days to look back
            max_items: Maximum number of transactions to fetch

        Returns:
            List of insider transactions
        """
        if not self._client:
            raise RuntimeError("Fetcher must be used as async context manager")

        transactions: list[InsiderTransaction] = []
        from_date = datetime.now() - timedelta(days=days_back)

        # Fetch the insider trading announcements list
        url = self._build_newsweb_url(from_date)

        try:
            response = await self._client.get(url)
            response.raise_for_status()

            # Parse the announcements list
            announcements = self._parse_announcements_list(response.text)

            for announcement in announcements[:max_items]:
                await asyncio.sleep(self.settings.request_delay_seconds)

                try:
                    tx = await self._fetch_announcement_details(announcement)
                    if tx:
                        transactions.append(tx)
                except Exception as e:
                    # Log error but continue with other announcements
                    print(f"Error fetching announcement {announcement.get('id')}: {e}")
                    continue

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to fetch from NewsWeb: {e}") from e

        return transactions

    def _build_newsweb_url(self, from_date: datetime) -> str:
        """Build the NewsWeb search URL for insider trading announcements."""
        # NewsWeb uses specific category IDs for different announcement types
        # Category 1-3 is "Meldepliktig handel" (Mandatory trade notifications)
        base = self.settings.newsweb_base_url
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = datetime.now().strftime("%Y-%m-%d")

        return (
            f"{base}/search?"
            f"category={self.INSIDER_CATEGORY_ID}&"
            f"fromDate={from_str}&"
            f"toDate={to_str}&"
            f"market=Oslo+Bors&"
            f"market=Euronext+Expand&"
            f"market=Euronext+Growth"
        )

    def _parse_announcements_list(self, html: str) -> list[dict]:
        """Parse the announcements list page to extract individual announcements."""
        soup = BeautifulSoup(html, "html.parser")
        announcements = []

        # Find announcement entries - NewsWeb uses table or list format
        rows = soup.select("table.announcements tr, .announcement-list .announcement-item, .message-list tr")

        for row in rows:
            # Try to extract announcement data
            link = row.select_one("a[href*='/message/']")
            if not link:
                continue

            href = link.get("href", "")
            announcement_id = self._extract_announcement_id(href)

            # Extract company ticker and date from row
            ticker_elem = row.select_one(".ticker, .symbol, td:nth-child(2)")
            date_elem = row.select_one(".date, .published, td:nth-child(1)")
            company_elem = row.select_one(".company, .issuer, td:nth-child(3)")

            announcements.append({
                "id": announcement_id,
                "url": f"{self.settings.newsweb_base_url}{href}" if href.startswith("/") else href,
                "ticker": ticker_elem.get_text(strip=True) if ticker_elem else "",
                "company_name": company_elem.get_text(strip=True) if company_elem else "",
                "date": date_elem.get_text(strip=True) if date_elem else "",
            })

        return announcements

    def _extract_announcement_id(self, href: str) -> str:
        """Extract announcement ID from URL."""
        match = re.search(r"/message/(\d+)", href)
        if match:
            return match.group(1)
        return hashlib.md5(href.encode()).hexdigest()[:12]

    async def _fetch_announcement_details(self, announcement: dict) -> Optional[InsiderTransaction]:
        """Fetch and parse detailed announcement data."""
        if not self._client or not announcement.get("url"):
            return None

        response = await self._client.get(announcement["url"])
        response.raise_for_status()

        return self._parse_insider_announcement(
            response.text,
            announcement["url"],
            announcement.get("id", ""),
        )

    def _parse_insider_announcement(
        self,
        html: str,
        source_url: str,
        announcement_id: str,
    ) -> Optional[InsiderTransaction]:
        """Parse an individual insider trading announcement page."""
        soup = BeautifulSoup(html, "html.parser")

        # Extract structured data from the announcement
        # Oslo Børs announcements typically have a structured format
        data = self._extract_announcement_data(soup)

        if not data:
            return None

        # Build the transaction object
        company = self._build_company(data)
        insider = self._build_insider(data)

        try:
            shares = self._parse_number(data.get("shares", "0"))
            price = self._parse_decimal(data.get("price", "0"))
            total_value = self._parse_decimal(data.get("total_value", "0"))

            # Calculate total if not provided
            if total_value == 0 and shares > 0 and price > 0:
                total_value = Decimal(shares) * price

            transaction = InsiderTransaction(
                id=announcement_id or hashlib.md5(source_url.encode()).hexdigest()[:12],
                company=company,
                insider=insider,
                transaction_type=self._parse_transaction_type(data.get("type", "")),
                transaction_date=self._parse_date(data.get("transaction_date", "")),
                publication_date=self._parse_date(data.get("publication_date", "")),
                shares=shares,
                price_per_share_nok=price,
                total_value_nok=total_value,
                shares_after_transaction=self._parse_number(data.get("holding_after")) if data.get("holding_after") else None,
                source_url=source_url,
                raw_data=data,
            )

            return transaction

        except (ValueError, TypeError) as e:
            print(f"Error parsing announcement data: {e}")
            return None

    def _extract_announcement_data(self, soup: BeautifulSoup) -> dict:
        """Extract structured data from an announcement page."""
        data = {}

        # Try to find a structured data table
        table = soup.select_one(".announcement-details, .message-content table, .pdmr-table")

        if table:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    # Map common field names
                    key_mapping = {
                        "issuer": "company_name",
                        "ticker": "ticker",
                        "symbol": "ticker",
                        "isin": "isin",
                        "person": "insider_name",
                        "name": "insider_name",
                        "pdmr": "insider_name",
                        "position": "insider_role",
                        "role": "insider_role",
                        "type": "type",
                        "transaction type": "type",
                        "nature": "type",
                        "volume": "shares",
                        "shares": "shares",
                        "quantity": "shares",
                        "price": "price",
                        "unit price": "price",
                        "amount": "total_value",
                        "total": "total_value",
                        "value": "total_value",
                        "aggregated volume": "total_value",
                        "date": "transaction_date",
                        "transaction date": "transaction_date",
                        "notification date": "publication_date",
                        "holding": "holding_after",
                        "shares after": "holding_after",
                    }

                    for search_key, mapped_key in key_mapping.items():
                        if search_key in key:
                            data[mapped_key] = value
                            break

        # Also try to extract from meta tags or JSON-LD
        meta_issuer = soup.select_one('meta[name="issuer"], meta[property="issuer"]')
        if meta_issuer and not data.get("company_name"):
            data["company_name"] = meta_issuer.get("content", "")

        # Extract from page title if needed
        title = soup.select_one("h1, .announcement-title")
        if title and not data.get("company_name"):
            title_text = title.get_text(strip=True)
            # Often the title contains the company name
            data["title"] = title_text

        return data

    def _build_company(self, data: dict) -> Company:
        """Build a Company object from extracted data."""
        ticker = data.get("ticker", "UNKNOWN")

        # Check cache first
        if ticker in self._company_cache:
            return self._company_cache[ticker]

        company = Company(
            ticker=ticker,
            name=data.get("company_name", ticker),
            isin=data.get("isin", ""),
            size_classification=CompanySize.UNKNOWN,
        )

        self._company_cache[ticker] = company
        return company

    def _build_insider(self, data: dict) -> Insider:
        """Build an Insider object from extracted data."""
        role_text = data.get("insider_role", "").lower()

        role = InsiderRole.OTHER
        if "ceo" in role_text or "adm.dir" in role_text or "chief executive" in role_text:
            role = InsiderRole.CEO
        elif "cfo" in role_text or "chief financial" in role_text or "finansdirektør" in role_text:
            role = InsiderRole.CFO
        elif "chairman" in role_text or "styreleder" in role_text or "chair" in role_text:
            role = InsiderRole.BOARD_CHAIR
        elif "board" in role_text or "styremedlem" in role_text or "director" in role_text:
            role = InsiderRole.BOARD_MEMBER
        elif "primary" in role_text or "primær" in role_text:
            role = InsiderRole.PRIMARY_INSIDER
        elif "related" in role_text or "nærstående" in role_text:
            role = InsiderRole.RELATED_PARTY

        return Insider(
            name=data.get("insider_name", "Unknown"),
            role=role,
            role_description=data.get("insider_role", ""),
        )

    def _parse_transaction_type(self, type_str: str) -> TransactionType:
        """Parse transaction type from string."""
        type_lower = type_str.lower()

        if "buy" in type_lower or "kjøp" in type_lower or "acquisition" in type_lower:
            return TransactionType.BUY
        elif "sell" in type_lower or "salg" in type_lower or "disposal" in type_lower:
            return TransactionType.SELL
        elif "gift" in type_lower or "gave" in type_lower:
            return TransactionType.GIFT
        elif "option" in type_lower or "opsjon" in type_lower or "exercise" in type_lower:
            return TransactionType.EXERCISE_OPTIONS

        return TransactionType.OTHER

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from various formats."""
        if not date_str:
            return datetime.now()

        # Common date formats used by Oslo Børs
        formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d.%m.%Y %H:%M",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        # If nothing works, return current time
        return datetime.now()

    def _parse_number(self, value_str: str) -> int:
        """Parse a number from string, handling various formats."""
        if not value_str:
            return 0

        # Remove common formatting
        cleaned = value_str.replace(" ", "").replace(",", "").replace("'", "")

        # Handle Norwegian decimal separator
        if "." in cleaned and cleaned.count(".") == 1:
            # Check if it's a decimal or thousand separator
            parts = cleaned.split(".")
            if len(parts[1]) == 3:  # Likely thousand separator
                cleaned = cleaned.replace(".", "")

        try:
            return int(float(cleaned))
        except ValueError:
            return 0

    def _parse_decimal(self, value_str: str) -> Decimal:
        """Parse a decimal number from string."""
        if not value_str:
            return Decimal("0")

        # Remove currency symbols and spaces
        cleaned = re.sub(r"[^\d.,\-]", "", value_str)

        # Handle Norwegian number format (space as thousand sep, comma as decimal)
        if "," in cleaned and "." in cleaned:
            # Both present - comma is likely decimal separator
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")

        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal("0")

    async def fetch_company_market_data(self, ticker: str) -> Optional[dict]:
        """Fetch market data for a company to determine market cap."""
        if not self._client:
            raise RuntimeError("Fetcher must be used as async context manager")

        # Oslo Børs provides market data through their website
        url = f"{self.settings.newsweb_base_url}/instrument/{ticker}"

        try:
            response = await self._client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            data = {}

            # Try to extract market cap and shares outstanding
            for label in soup.select(".instrument-data dt, .key-figure-label"):
                key = label.get_text(strip=True).lower()
                value_elem = label.find_next_sibling("dd") or label.find_next_sibling(".key-figure-value")

                if value_elem:
                    value = value_elem.get_text(strip=True)

                    if "market cap" in key or "markedsverdi" in key:
                        data["market_cap"] = self._parse_market_cap(value)
                    elif "shares" in key or "aksjer" in key:
                        data["shares_outstanding"] = self._parse_number(value)

            return data if data else None

        except httpx.HTTPError:
            return None

    def _parse_market_cap(self, value: str) -> Optional[Decimal]:
        """Parse market cap, handling millions/billions abbreviations."""
        if not value:
            return None

        value_lower = value.lower()
        multiplier = Decimal("1")

        if "mrd" in value_lower or "bn" in value_lower or "b" in value_lower:
            multiplier = Decimal("1000000000")
        elif "mill" in value_lower or "mn" in value_lower or "m" in value_lower:
            multiplier = Decimal("1000000")

        # Extract the numeric part
        numeric = re.sub(r"[^\d.,]", "", value)
        if "," in numeric:
            numeric = numeric.replace(",", ".")

        try:
            return Decimal(numeric) * multiplier
        except Exception:
            return None
