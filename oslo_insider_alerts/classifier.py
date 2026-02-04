"""Company size classifier for filtering small and medium cap companies."""

from decimal import Decimal
from typing import Optional

from .config import CompanySizeFilter
from .fetcher import OsloBorsDataFetcher
from .models import Company, CompanySize


class CompanySizeClassifier:
    """Classifies companies by market cap and filters for small/medium cap."""

    def __init__(
        self,
        filter_config: Optional[CompanySizeFilter] = None,
        fetcher: Optional[OsloBorsDataFetcher] = None,
    ):
        self.config = filter_config or CompanySizeFilter()
        self.fetcher = fetcher
        self._market_cap_cache: dict[str, Optional[Decimal]] = {}

    def classify(self, company: Company) -> CompanySize:
        """Classify a company based on its market cap.

        Args:
            company: The company to classify

        Returns:
            CompanySize classification
        """
        market_cap = company.market_cap_nok

        if market_cap is None:
            # Try to get from cache
            market_cap = self._market_cap_cache.get(company.ticker)

        if market_cap is None:
            return CompanySize.UNKNOWN

        # Convert thresholds to NOK (from billions)
        small_cap_threshold = Decimal(str(self.config.small_cap_max_nok_billions)) * Decimal("1e9")
        medium_cap_threshold = Decimal(str(self.config.medium_cap_max_nok_billions)) * Decimal("1e9")

        if market_cap <= small_cap_threshold:
            return CompanySize.SMALL
        elif market_cap <= medium_cap_threshold:
            return CompanySize.MEDIUM
        else:
            return CompanySize.LARGE

    async def classify_with_fetch(self, company: Company) -> CompanySize:
        """Classify a company, fetching market data if needed.

        Args:
            company: The company to classify

        Returns:
            CompanySize classification
        """
        # Check if we already have market cap
        if company.market_cap_nok is not None:
            return self.classify(company)

        # Check cache
        if company.ticker in self._market_cap_cache:
            cached_cap = self._market_cap_cache[company.ticker]
            if cached_cap is not None:
                company.market_cap_nok = cached_cap
                return self.classify(company)

        # Fetch market data if we have a fetcher
        if self.fetcher:
            market_data = await self.fetcher.fetch_company_market_data(company.ticker)
            if market_data and "market_cap" in market_data:
                company.market_cap_nok = market_data["market_cap"]
                company.shares_outstanding = market_data.get("shares_outstanding")
                self._market_cap_cache[company.ticker] = company.market_cap_nok
                return self.classify(company)

        return CompanySize.UNKNOWN

    def is_target_company(self, company: Company) -> bool:
        """Check if a company matches our target criteria (small/medium cap).

        Args:
            company: The company to check

        Returns:
            True if the company should be monitored
        """
        # Always exclude if in exclude list
        if company.ticker in self.config.exclude_tickers:
            return False

        # Always include if in include list
        if company.ticker in self.config.include_tickers:
            return True

        # Check size classification
        size = self.classify(company)

        # Include small and medium cap companies
        # Also include unknown (they might be small/medium, will be verified later)
        return size in (CompanySize.SMALL, CompanySize.MEDIUM, CompanySize.UNKNOWN)

    async def is_target_company_with_fetch(self, company: Company) -> bool:
        """Check if a company matches target criteria, fetching data if needed.

        Args:
            company: The company to check

        Returns:
            True if the company should be monitored
        """
        # Always exclude if in exclude list
        if company.ticker in self.config.exclude_tickers:
            return False

        # Always include if in include list
        if company.ticker in self.config.include_tickers:
            return True

        # Classify with potential data fetch
        size = await self.classify_with_fetch(company)

        # Include small and medium cap companies
        return size in (CompanySize.SMALL, CompanySize.MEDIUM)

    def update_cache(self, ticker: str, market_cap: Decimal) -> None:
        """Update the market cap cache for a ticker.

        Args:
            ticker: Company ticker symbol
            market_cap: Market cap in NOK
        """
        self._market_cap_cache[ticker] = market_cap

    def clear_cache(self) -> None:
        """Clear the market cap cache."""
        self._market_cap_cache.clear()

    def get_cached_market_cap(self, ticker: str) -> Optional[Decimal]:
        """Get cached market cap for a ticker.

        Args:
            ticker: Company ticker symbol

        Returns:
            Cached market cap or None
        """
        return self._market_cap_cache.get(ticker)


# Default Oslo Børs small/medium cap tickers (as of 2024)
# These are companies typically in the small/medium cap segment
OSLO_SMALL_MID_CAP_TICKERS = [
    # Small cap examples
    "AGAS", "AKSO", "ARCH", "BAKKA", "BORR",
    "BOUV", "CADLR", "CLOUD", "CONTE", "CRAYON",
    "ECIT", "ENDUR", "ENTRA", "FLEX", "FLYR",
    "GIG", "HAFNI", "HMONY", "HUNT", "INSR",
    "KALERA", "KID", "KOG", "LINK", "MULTI",
    "NORAM", "NRC", "OTOVO", "PARB", "PEN",
    "PEXIP", "PHO", "PLCS", "PROTCT", "PROT",
    "PSE", "REACH", "RECSI", "RIVER", "SAGA",
    "SATS", "SCANA", "SCHB", "SDRL", "SIKRI",
    "SOFF", "SOLON", "SPOL", "THIN", "VOLUE",
    "WSTEP", "XXL", "ZAPTEC",
    # Medium cap examples
    "AKRBP", "ATEA", "AUTO", "BEWI", "BWE",
    "ELMRA", "EPR", "FJORD", "HAVI", "HEX",
    "KIT", "LSG", "MPCC", "NEL", "NHY",
    "NTS", "OKEA", "ORK", "PCIB", "RECSI",
    "SCATC", "SCHB", "SNI", "SPOL", "VEI",
]
