from __future__ import annotations

from datetime import date
from typing import cast

from packages.data.providers import PriceRow, PriceRows

TRADING_DAYS_6M = 126
TRADING_DAYS_12M = 252


def add_moving_averages(prices: PriceRows) -> PriceRows:
    data = sorted(prices, key=_row_date)
    closes = [float(row["close"]) for row in data]
    enriched: PriceRows = []
    for index, row in enumerate(data):
        new_row = cast(PriceRow, dict(row))
        new_row["sma50"] = _rolling_average(closes, index, 50)
        new_row["sma100"] = _rolling_average(closes, index, 100)
        new_row["sma200"] = _rolling_average(closes, index, 200)
        enriched.append(new_row)
    return enriched


def percent_distance(value: float, reference: float) -> float:
    if reference == 0:
        return 0.0
    return (value - reference) / reference


def high_drawdown(prices: PriceRows, window: int = TRADING_DAYS_12M) -> float:
    recent = sorted(prices, key=_row_date)[-window:]
    if not recent:
        return 0.0
    current = float(recent[-1]["close"])
    high = max(float(row["high"]) for row in recent)
    return percent_distance(current, high)


def momentum(prices: PriceRows, periods: int) -> float | None:
    sorted_prices = sorted(prices, key=_row_date)
    if len(sorted_prices) <= periods:
        return None
    current = float(sorted_prices[-1]["close"])
    past = float(sorted_prices[-periods - 1]["close"])
    return percent_distance(current, past)


def _rolling_average(values: list[float], index: int, window: int) -> float | None:
    if index + 1 < window:
        return None
    window_values = values[index - window + 1 : index + 1]
    return sum(window_values) / window


def _row_date(row: PriceRow) -> date:
    return row["date"]
