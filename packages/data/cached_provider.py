from __future__ import annotations

from datetime import date

from packages.data.cache import DuckDBCache
from packages.data.models import CompanyProfile, Fundamentals
from packages.data.providers import MarketDataProvider, PriceRows


class CachedMarketDataProvider(MarketDataProvider):
    """Read-through cache wrapper for any MarketDataProvider."""

    def __init__(self, provider: MarketDataProvider, cache: DuckDBCache) -> None:
        self.provider = provider
        self.cache = cache

    def get_price_history(self, ticker: str, start: date, end: date) -> PriceRows:
        cached = self.cache.get_price_history(ticker, start, end)
        if cached:
            return cached
        prices = self.provider.get_price_history(ticker, start, end)
        self.cache.put_price_history(ticker, prices)
        return prices

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        cached = self.cache.get_fundamentals(ticker)
        if cached is not None:
            return cached
        fundamentals = self.provider.get_fundamentals(ticker)
        self.cache.put_fundamentals(fundamentals)
        return fundamentals

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        cached = self.cache.get_company_profile(ticker)
        if cached is not None:
            return cached
        profile = self.provider.get_company_profile(ticker)
        self.cache.put_company_profile(profile)
        return profile
