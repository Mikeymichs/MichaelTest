from __future__ import annotations

from datetime import date
from typing import Any

import yfinance as yf

from packages.data.models import CompanyProfile, Fundamentals
from packages.data.providers import MarketDataProvider, PriceRows


class YFinanceProvider(MarketDataProvider):
    """Starter yfinance adapter kept behind the MarketDataProvider interface."""

    def get_price_history(self, ticker: str, start: date, end: date) -> PriceRows:
        history: Any = yf.Ticker(ticker).history(
            start=start.isoformat(),
            end=end.isoformat(),
            auto_adjust=False,
        )
        history = history.reset_index()
        rows: PriceRows = []
        for record in history.to_dict("records"):
            record_date = record.get("Date") or record.get("date")
            if hasattr(record_date, "date"):
                record_date = record_date.date()
            rows.append(
                {
                    "date": record_date,
                    "open": float(record.get("Open") or record.get("open") or 0.0),
                    "high": float(record.get("High") or record.get("high") or 0.0),
                    "low": float(record.get("Low") or record.get("low") or 0.0),
                    "close": float(record.get("Close") or record.get("close") or 0.0),
                    "volume": int(record.get("Volume") or record.get("volume") or 0),
                }
            )
        return rows

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        info: dict[str, Any] = yf.Ticker(ticker).info
        return Fundamentals(
            ticker=ticker.upper(),
            revenue_growth=info.get("revenueGrowth"),
            gross_margin=info.get("grossMargins"),
            operating_margin=info.get("operatingMargins"),
            free_cash_flow_margin=None,
            return_on_equity=info.get("returnOnEquity"),
            debt_to_equity=_scale_percent_metric(info.get("debtToEquity")),
            current_ratio=info.get("currentRatio"),
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            price_to_sales=info.get("priceToSalesTrailing12Months"),
            ev_to_ebitda=info.get("enterpriseToEbitda"),
        )

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        info: dict[str, Any] = yf.Ticker(ticker).info
        return CompanyProfile(
            ticker=ticker.upper(),
            name=info.get("longName") or ticker.upper(),
            sector=info.get("sector"),
            industry=info.get("industry"),
            exchange=info.get("exchange"),
            currency=info.get("currency") or "USD",
        )


def _scale_percent_metric(value: object) -> float | None:
    if not isinstance(value, int | float):
        return None
    return float(value) / 100 if value > 10 else float(value)
