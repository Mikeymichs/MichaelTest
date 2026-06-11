from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, SupportsFloat, cast

from packages.data.cache import DuckDBCache
from packages.data.cached_provider import CachedMarketDataProvider
from packages.data.providers import MarketDataProvider, MockMarketDataProvider, PriceRows
from packages.indicators.technical import (
    TRADING_DAYS_6M,
    TRADING_DAYS_12M,
    add_moving_averages,
    high_drawdown,
    momentum,
    percent_distance,
)
from packages.screeners.models import (
    CandidateClass,
    ScreenerResult,
    StrategyConfig,
    TechnicalSnapshot,
)
from packages.screeners.scoring import (
    score_quality,
    score_risk,
    score_technical_setup,
    score_valuation,
    total_score,
)

MIN_REQUIRED_BARS = 252


def load_strategy_config(path: Path) -> StrategyConfig:
    return StrategyConfig.model_validate(_parse_simple_yaml(path))


def build_provider(config: StrategyConfig) -> MarketDataProvider:
    if config.provider != "mock":
        raise ValueError(
            f"Unsupported provider '{config.provider}'. The default local provider is 'mock'."
        )
    return CachedMarketDataProvider(MockMarketDataProvider(), DuckDBCache(config.cache_path))


def screen_us(
    config: StrategyConfig, provider: MarketDataProvider | None = None
) -> list[ScreenerResult]:
    active_provider = provider or build_provider(config)
    results = [screen_ticker(ticker, config, active_provider) for ticker in config.tickers]
    ranked = sorted(results, key=lambda result: result.total_score, reverse=True)
    with_ranks = [
        result.model_copy(update={"rank": index}) for index, result in enumerate(ranked, start=1)
    ]
    config.evidence_dir.mkdir(parents=True, exist_ok=True)
    return [write_evidence(result, config.evidence_dir) for result in with_ranks]


def screen_ticker(
    ticker: str,
    config: StrategyConfig,
    provider: MarketDataProvider,
) -> ScreenerResult:
    ticker = ticker.upper()
    start = date.fromisoformat(config.start)
    end = date.fromisoformat(config.end)
    prices = provider.get_price_history(ticker, start, end)
    profile = provider.get_company_profile(ticker)
    fundamentals = provider.get_fundamentals(ticker)

    if len(prices) < MIN_REQUIRED_BARS:
        technicals = TechnicalSnapshot(
            current_price=None,
            sma50=None,
            sma100=None,
            sma200=None,
            distance_to_sma200=None,
            drawdown_52w=None,
            momentum_6m=None,
            momentum_12m=None,
        )
        return ScreenerResult(
            ticker=ticker,
            signal=CandidateClass.INSUFFICIENT_DATA,
            total_score=0.0,
            quality_score=0.0,
            valuation_score=0.0,
            technical_setup_score=0.0,
            risk_score=0.0,
            risk_flags=["insufficient_price_history"],
            profile=profile,
            fundamentals=fundamentals,
            technicals=technicals,
            scoring_explanation={"data": [f"Only {len(prices)} price bars available"]},
        )

    technicals = calculate_technicals(prices)
    quality = score_quality(fundamentals)
    valuation = score_valuation(fundamentals)
    technical = score_technical_setup(
        technicals.distance_to_sma200,
        technicals.drawdown_52w,
        technicals.momentum_6m,
        technicals.momentum_12m,
    )
    risk = score_risk(fundamentals, technicals.drawdown_52w)
    risk_flags = detect_risk_flags(fundamentals, technicals)
    total = total_score(quality.score, valuation.score, technical.score, risk.score)
    signal = classify_candidate(
        quality.score, valuation.score, technical.score, risk.score, risk_flags
    )
    return ScreenerResult(
        ticker=ticker,
        signal=signal,
        total_score=total,
        quality_score=quality.score,
        valuation_score=valuation.score,
        technical_setup_score=technical.score,
        risk_score=risk.score,
        risk_flags=risk_flags,
        profile=profile,
        fundamentals=fundamentals,
        technicals=technicals,
        scoring_explanation={
            "quality": quality.explanation,
            "valuation": valuation.explanation,
            "technical": technical.explanation,
            "risk": risk.explanation,
        },
    )


def calculate_technicals(prices: PriceRows) -> TechnicalSnapshot:
    enriched = add_moving_averages(prices)
    latest = enriched[-1]
    current_price = float(latest["close"])
    sma50 = _none_if_nan(latest["sma50"])
    sma100 = _none_if_nan(latest["sma100"])
    sma200 = _none_if_nan(latest["sma200"])
    distance_to_sma200 = None if sma200 is None else percent_distance(current_price, sma200)
    return TechnicalSnapshot(
        current_price=current_price,
        sma50=sma50,
        sma100=sma100,
        sma200=sma200,
        distance_to_sma200=distance_to_sma200,
        drawdown_52w=high_drawdown(enriched, TRADING_DAYS_12M),
        momentum_6m=momentum(enriched, TRADING_DAYS_6M),
        momentum_12m=momentum(enriched, TRADING_DAYS_12M),
    )


def classify_candidate(
    quality_score: float,
    valuation_score: float,
    technical_score: float,
    risk_score: float,
    risk_flags: list[str],
) -> CandidateClass:
    severe_flags = {"high_leverage", "poor_liquidity", "deep_drawdown"}
    if severe_flags.intersection(risk_flags) or quality_score < 45 or risk_score < 35:
        return CandidateClass.AVOID
    if quality_score >= 70 and valuation_score >= 45 and technical_score >= 60 and risk_score >= 55:
        return CandidateClass.BUY_RESEARCH
    return CandidateClass.WATCHLIST


def detect_risk_flags(fundamentals: Any, technicals: TechnicalSnapshot) -> list[str]:
    flags: list[str] = []
    if fundamentals.debt_to_equity is not None and fundamentals.debt_to_equity > 2.0:
        flags.append("high_leverage")
    if fundamentals.current_ratio is not None and fundamentals.current_ratio < 0.8:
        flags.append("poor_liquidity")
    if technicals.drawdown_52w is not None and technicals.drawdown_52w < -0.35:
        flags.append("deep_drawdown")
    if technicals.distance_to_sma200 is not None and technicals.distance_to_sma200 > 0.25:
        flags.append("extended_above_sma200")
    return flags or ["none"]


def write_evidence(result: ScreenerResult, evidence_dir: Path) -> ScreenerResult:
    evidence_path = evidence_dir / f"{result.rank:02d}_{result.ticker}.json"
    payload = result.model_dump(mode="json")
    payload["evidence_file"] = str(evidence_path)
    evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return result.model_copy(update={"evidence_file": evidence_path})


def _none_if_nan(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, SupportsFloat):
        return float(value)
    return float(str(value))


def _parse_simple_yaml(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    current_list_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-") and current_list_key is not None:
            values = cast(list[str], data[current_list_key])
            values.append(line[1:].strip().strip('"'))
            continue
        key, value = line.split(":", 1)
        current_list_key = None
        value = value.strip()
        if not value:
            data[key] = []
            current_list_key = key
        else:
            data[key] = value.strip('"')
    return data
