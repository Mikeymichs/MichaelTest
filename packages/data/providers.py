from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from math import sin
from typing import NotRequired, TypedDict

from packages.data.models import CompanyProfile, Fundamentals


class PriceRow(TypedDict):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    sma50: NotRequired[float | None]
    sma100: NotRequired[float | None]
    sma200: NotRequired[float | None]


PriceRows = list[PriceRow]


class MarketDataProvider(ABC):
    """Provider abstraction for market data and fundamentals."""

    @abstractmethod
    def get_price_history(self, ticker: str, start: date, end: date) -> PriceRows:
        """Return OHLCV price history rows with date, open, high, low, close, volume keys."""

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> Fundamentals:
        """Return company fundamentals for deterministic screening."""

    @abstractmethod
    def get_company_profile(self, ticker: str) -> CompanyProfile:
        """Return company profile metadata."""


class OpenBBProviderInterface(MarketDataProvider):
    """Optional OpenBB integration point for a future concrete adapter."""


class MockMarketDataProvider(MarketDataProvider):
    """Deterministic local provider used by tests and the default CLI strategy."""

    _fundamentals: dict[str, Fundamentals] = {
        "AAPL": Fundamentals(
            "AAPL", 0.06, 0.46, 0.31, 0.24, 1.45, 1.45, 0.99, 30.0, 26.0, 7.2, 22.0
        ),
        "MSFT": Fundamentals(
            "MSFT", 0.13, 0.69, 0.44, 0.30, 0.37, 0.35, 1.25, 34.0, 29.0, 12.0, 24.0
        ),
        "NVDA": Fundamentals(
            "NVDA", 1.20, 0.74, 0.55, 0.39, 0.95, 0.20, 3.5, 48.0, 32.0, 25.0, 38.0
        ),
        "GOOGL": Fundamentals(
            "GOOGL", 0.11, 0.57, 0.29, 0.22, 0.29, 0.10, 2.1, 25.0, 21.0, 6.0, 17.0
        ),
        "AMZN": Fundamentals(
            "AMZN", 0.12, 0.48, 0.10, 0.08, 0.18, 0.70, 1.05, 42.0, 31.0, 3.2, 19.0
        ),
    }
    _profiles: dict[str, CompanyProfile] = {
        "AAPL": CompanyProfile("AAPL", "Apple Inc.", "Technology"),
        "MSFT": CompanyProfile("MSFT", "Microsoft Corporation", "Technology"),
        "NVDA": CompanyProfile("NVDA", "NVIDIA Corporation", "Technology"),
        "GOOGL": CompanyProfile("GOOGL", "Alphabet Inc.", "Communication Services"),
        "AMZN": CompanyProfile("AMZN", "Amazon.com, Inc.", "Consumer Discretionary"),
    }
    _base_prices: dict[str, float] = {
        "AAPL": 195.0,
        "MSFT": 425.0,
        "NVDA": 120.0,
        "GOOGL": 175.0,
        "AMZN": 185.0,
    }

    def get_price_history(self, ticker: str, start: date, end: date) -> PriceRows:
        ticker = ticker.upper()
        days = max((end - start).days + 1, 0)
        rows: PriceRows = []
        base_price = self._base_prices.get(ticker, 100.0)
        ticker_bias = (sum(ord(char) for char in ticker) % 17) / 1000
        for offset in range(days):
            current_date = start + timedelta(days=offset)
            if current_date.weekday() >= 5:
                continue
            trend = 1 + (offset * (0.00045 + ticker_bias / 12))
            cycle = 1 + (sin(offset / 12) * 0.035)
            close = round(base_price * trend * cycle, 2)
            rows.append(
                {
                    "date": current_date,
                    "open": round(close * 0.997, 2),
                    "high": round(close * 1.012, 2),
                    "low": round(close * 0.988, 2),
                    "close": close,
                    "volume": 1_000_000 + (offset * 12_345) % 500_000,
                }
            )
        return rows

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        ticker = ticker.upper()
        return self._fundamentals.get(ticker, Fundamentals(ticker=ticker))

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        ticker = ticker.upper()
        return self._profiles.get(ticker, CompanyProfile(ticker=ticker, name=ticker))
