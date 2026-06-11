from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, cast


@dataclass(frozen=True)
class PriceBar:
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int

    def model_dump(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Fundamentals:
    ticker: str
    revenue_growth: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    free_cash_flow_margin: float | None = None
    return_on_equity: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None
    price_to_sales: float | None = None
    ev_to_ebitda: float | None = None

    def model_dump(self) -> dict[str, object]:
        return asdict(self)

    def model_copy(self, *, update: dict[str, object] | None = None) -> Fundamentals:
        data = self.model_dump()
        if update:
            data.update(update)
        return Fundamentals.model_validate(data)

    @classmethod
    def model_validate(cls, data: dict[str, object]) -> Fundamentals:
        return cls(
            ticker=str(data["ticker"]),
            revenue_growth=cast(float | None, data.get("revenue_growth")),
            gross_margin=cast(float | None, data.get("gross_margin")),
            operating_margin=cast(float | None, data.get("operating_margin")),
            free_cash_flow_margin=cast(float | None, data.get("free_cash_flow_margin")),
            return_on_equity=cast(float | None, data.get("return_on_equity")),
            debt_to_equity=cast(float | None, data.get("debt_to_equity")),
            current_ratio=cast(float | None, data.get("current_ratio")),
            pe_ratio=cast(float | None, data.get("pe_ratio")),
            forward_pe=cast(float | None, data.get("forward_pe")),
            price_to_sales=cast(float | None, data.get("price_to_sales")),
            ev_to_ebitda=cast(float | None, data.get("ev_to_ebitda")),
        )


@dataclass(frozen=True)
class CompanyProfile:
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None
    currency: str = "USD"

    def model_dump(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> CompanyProfile:
        return cls(
            ticker=str(data["ticker"]),
            name=str(data["name"]),
            sector=cast(str | None, data.get("sector")),
            industry=cast(str | None, data.get("industry")),
            exchange=cast(str | None, data.get("exchange")),
            currency=str(data.get("currency") or "USD"),
        )
