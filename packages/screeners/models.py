from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import cast

from packages.data.models import CompanyProfile, Fundamentals


class CandidateClass(StrEnum):
    BUY_RESEARCH = "BUY_RESEARCH"
    WATCHLIST = "WATCHLIST"
    AVOID = "AVOID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class StrategyConfig:
    tickers: list[str]
    start: str
    end: str
    provider: str = "mock"
    cache_path: Path = Path("research/cache.duckdb")
    evidence_dir: Path = Path("research/evidence")
    report_path: Path = Path("research/reports/200dma-quality.md")

    @classmethod
    def model_validate(cls, data: dict[str, object]) -> StrategyConfig:
        return cls(
            tickers=cast(list[str], data["tickers"]),
            start=str(data["start"]),
            end=str(data["end"]),
            provider=str(data.get("provider") or "mock"),
            cache_path=Path(str(data.get("cache_path") or "research/cache.duckdb")),
            evidence_dir=Path(str(data.get("evidence_dir") or "research/evidence")),
            report_path=Path(str(data.get("report_path") or "research/reports/200dma-quality.md")),
        )


@dataclass(frozen=True)
class TechnicalSnapshot:
    current_price: float | None
    sma50: float | None
    sma100: float | None
    sma200: float | None
    distance_to_sma200: float | None
    drawdown_52w: float | None
    momentum_6m: float | None
    momentum_12m: float | None


@dataclass(frozen=True)
class ScreenerResult:
    ticker: str
    signal: CandidateClass
    total_score: float
    quality_score: float
    valuation_score: float
    technical_setup_score: float
    risk_score: float
    risk_flags: list[str]
    profile: CompanyProfile
    fundamentals: Fundamentals
    technicals: TechnicalSnapshot
    scoring_explanation: dict[str, list[str]]
    rank: int | None = None
    evidence_file: Path | None = None

    def model_copy(self, *, update: dict[str, object] | None = None) -> ScreenerResult:
        return replace(self, **(update or {}))  # type: ignore[arg-type]

    def model_dump(self, mode: str = "python") -> dict[str, object]:
        data: dict[str, object] = asdict(self)
        data["signal"] = self.signal.value
        if mode == "json":
            return cast(dict[str, object], _jsonify(data))
        return data


def _jsonify(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonify(item) for item in value]
    if hasattr(value, "isoformat"):
        isoformat = value.isoformat
        return str(isoformat())
    return value
