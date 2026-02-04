"""Tests for company size classifier."""

from decimal import Decimal

import pytest

from oslo_insider_alerts.classifier import CompanySizeClassifier
from oslo_insider_alerts.config import CompanySizeFilter
from oslo_insider_alerts.models import Company, CompanySize


@pytest.fixture
def filter_config() -> CompanySizeFilter:
    """Create test filter configuration."""
    return CompanySizeFilter(
        small_cap_max_nok_billions=5.0,
        medium_cap_max_nok_billions=25.0,
        include_tickers=["ALWAYS"],
        exclude_tickers=["NEVER"],
    )


@pytest.fixture
def classifier(filter_config: CompanySizeFilter) -> CompanySizeClassifier:
    """Create a classifier instance."""
    return CompanySizeClassifier(filter_config=filter_config)


class TestCompanySizeClassifier:
    """Tests for CompanySizeClassifier."""

    def test_classify_small_cap(self, classifier: CompanySizeClassifier) -> None:
        """Test classification of small cap companies."""
        company = Company(
            ticker="SMALL",
            name="Small Company ASA",
            market_cap_nok=Decimal("2000000000"),  # 2 billion NOK
        )

        size = classifier.classify(company)
        assert size == CompanySize.SMALL

    def test_classify_medium_cap(self, classifier: CompanySizeClassifier) -> None:
        """Test classification of medium cap companies."""
        company = Company(
            ticker="MEDIUM",
            name="Medium Company ASA",
            market_cap_nok=Decimal("10000000000"),  # 10 billion NOK
        )

        size = classifier.classify(company)
        assert size == CompanySize.MEDIUM

    def test_classify_large_cap(self, classifier: CompanySizeClassifier) -> None:
        """Test classification of large cap companies."""
        company = Company(
            ticker="LARGE",
            name="Large Company ASA",
            market_cap_nok=Decimal("50000000000"),  # 50 billion NOK
        )

        size = classifier.classify(company)
        assert size == CompanySize.LARGE

    def test_classify_unknown_without_market_cap(
        self, classifier: CompanySizeClassifier
    ) -> None:
        """Test classification when market cap is unknown."""
        company = Company(
            ticker="UNKNOWN",
            name="Unknown Company ASA",
            market_cap_nok=None,
        )

        size = classifier.classify(company)
        assert size == CompanySize.UNKNOWN

    def test_is_target_company_small_cap(self, classifier: CompanySizeClassifier) -> None:
        """Test that small cap is a target company."""
        company = Company(
            ticker="SMALL",
            name="Small Company ASA",
            market_cap_nok=Decimal("2000000000"),
        )

        assert classifier.is_target_company(company) is True

    def test_is_target_company_medium_cap(self, classifier: CompanySizeClassifier) -> None:
        """Test that medium cap is a target company."""
        company = Company(
            ticker="MEDIUM",
            name="Medium Company ASA",
            market_cap_nok=Decimal("10000000000"),
        )

        assert classifier.is_target_company(company) is True

    def test_is_not_target_company_large_cap(
        self, classifier: CompanySizeClassifier
    ) -> None:
        """Test that large cap is not a target company."""
        company = Company(
            ticker="LARGE",
            name="Large Company ASA",
            market_cap_nok=Decimal("50000000000"),
        )

        assert classifier.is_target_company(company) is False

    def test_include_ticker_override(self, classifier: CompanySizeClassifier) -> None:
        """Test that include_tickers forces inclusion."""
        company = Company(
            ticker="ALWAYS",
            name="Always Include ASA",
            market_cap_nok=Decimal("100000000000"),  # 100 billion (large cap)
        )

        # Even though it's large cap, it should be included
        assert classifier.is_target_company(company) is True

    def test_exclude_ticker_override(self, classifier: CompanySizeClassifier) -> None:
        """Test that exclude_tickers forces exclusion."""
        company = Company(
            ticker="NEVER",
            name="Never Include ASA",
            market_cap_nok=Decimal("1000000000"),  # 1 billion (small cap)
        )

        # Even though it's small cap, it should be excluded
        assert classifier.is_target_company(company) is False

    def test_cache_operations(self, classifier: CompanySizeClassifier) -> None:
        """Test cache update and retrieval."""
        classifier.update_cache("CACHED", Decimal("5000000000"))

        cached = classifier.get_cached_market_cap("CACHED")
        assert cached == Decimal("5000000000")

        # Test with a company that uses cache
        company = Company(
            ticker="CACHED",
            name="Cached Company ASA",
        )

        # Should use cached value for classification
        size = classifier.classify(company)
        assert size == CompanySize.SMALL  # 5 billion is at the threshold

    def test_clear_cache(self, classifier: CompanySizeClassifier) -> None:
        """Test cache clearing."""
        classifier.update_cache("TEST", Decimal("1000000000"))
        assert classifier.get_cached_market_cap("TEST") is not None

        classifier.clear_cache()
        assert classifier.get_cached_market_cap("TEST") is None

    def test_boundary_small_cap(self, classifier: CompanySizeClassifier) -> None:
        """Test boundary at small cap threshold."""
        # Exactly at 5 billion threshold
        company = Company(
            ticker="BOUNDARY",
            name="Boundary Company ASA",
            market_cap_nok=Decimal("5000000000"),
        )

        size = classifier.classify(company)
        assert size == CompanySize.SMALL  # At threshold should be small

    def test_boundary_medium_cap(self, classifier: CompanySizeClassifier) -> None:
        """Test boundary at medium cap threshold."""
        # Exactly at 25 billion threshold
        company = Company(
            ticker="BOUNDARY",
            name="Boundary Company ASA",
            market_cap_nok=Decimal("25000000000"),
        )

        size = classifier.classify(company)
        assert size == CompanySize.MEDIUM  # At threshold should be medium
