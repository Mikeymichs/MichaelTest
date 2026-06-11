from __future__ import annotations

from dataclasses import dataclass

from packages.data.models import Fundamentals


@dataclass(frozen=True)
class ScoreBreakdown:
    score: float
    explanation: list[str]


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return round(max(minimum, min(maximum, value)), 2)


def scaled_score(value: float | None, low: float, high: float, *, inverse: bool = False) -> float:
    if value is None:
        return 50.0
    if high == low:
        return 50.0
    raw = (value - low) / (high - low)
    if inverse:
        raw = 1 - raw
    return clamp(raw * 100)


def score_quality(fundamentals: Fundamentals) -> ScoreBreakdown:
    metrics = {
        "revenue_growth": scaled_score(fundamentals.revenue_growth, -0.05, 0.25),
        "gross_margin": scaled_score(fundamentals.gross_margin, 0.20, 0.70),
        "operating_margin": scaled_score(fundamentals.operating_margin, 0.05, 0.35),
        "free_cash_flow_margin": scaled_score(fundamentals.free_cash_flow_margin, 0.00, 0.25),
        "return_on_equity": scaled_score(fundamentals.return_on_equity, 0.05, 0.35),
    }
    score = clamp(sum(metrics.values()) / len(metrics))
    explanation = [f"{name} contributed {value:.2f}/100" for name, value in metrics.items()]
    return ScoreBreakdown(score=score, explanation=explanation)


def score_valuation(fundamentals: Fundamentals) -> ScoreBreakdown:
    metrics = {
        "pe_ratio": scaled_score(fundamentals.pe_ratio, 12.0, 45.0, inverse=True),
        "forward_pe": scaled_score(fundamentals.forward_pe, 10.0, 35.0, inverse=True),
        "price_to_sales": scaled_score(fundamentals.price_to_sales, 2.0, 15.0, inverse=True),
        "ev_to_ebitda": scaled_score(fundamentals.ev_to_ebitda, 8.0, 30.0, inverse=True),
    }
    score = clamp(sum(metrics.values()) / len(metrics))
    explanation = [
        f"{name} valuation contributed {value:.2f}/100" for name, value in metrics.items()
    ]
    return ScoreBreakdown(score=score, explanation=explanation)


def score_technical_setup(
    distance_to_sma200: float | None,
    drawdown_52w: float | None,
    momentum_6m: float | None,
    momentum_12m: float | None,
) -> ScoreBreakdown:
    if None in (distance_to_sma200, drawdown_52w, momentum_6m, momentum_12m):
        return ScoreBreakdown(score=0.0, explanation=["Insufficient technical history for scoring"])
    assert distance_to_sma200 is not None
    assert drawdown_52w is not None
    assert momentum_6m is not None
    assert momentum_12m is not None
    distance_score = clamp(100 - abs(distance_to_sma200) * 500)
    drawdown_score = scaled_score(drawdown_52w, -0.35, -0.02)
    momentum_6m_score = scaled_score(momentum_6m, -0.15, 0.25)
    momentum_12m_score = scaled_score(momentum_12m, -0.25, 0.40)
    score = clamp(
        (distance_score * 0.40)
        + (drawdown_score * 0.20)
        + (momentum_6m_score * 0.20)
        + (momentum_12m_score * 0.20)
    )
    return ScoreBreakdown(
        score=score,
        explanation=[
            f"SMA200 distance score {distance_score:.2f}/100 from {distance_to_sma200:.2%}",
            f"52-week drawdown score {drawdown_score:.2f}/100 from {drawdown_52w:.2%}",
            f"6-month momentum score {momentum_6m_score:.2f}/100 from {momentum_6m:.2%}",
            f"12-month momentum score {momentum_12m_score:.2f}/100 from {momentum_12m:.2%}",
        ],
    )


def score_risk(fundamentals: Fundamentals, drawdown_52w: float | None) -> ScoreBreakdown:
    debt_score = scaled_score(fundamentals.debt_to_equity, 0.0, 2.5, inverse=True)
    liquidity_score = scaled_score(fundamentals.current_ratio, 0.6, 2.0)
    drawdown_score = 50.0 if drawdown_52w is None else scaled_score(drawdown_52w, -0.45, -0.05)
    score = clamp((debt_score * 0.40) + (liquidity_score * 0.35) + (drawdown_score * 0.25))
    return ScoreBreakdown(
        score=score,
        explanation=[
            f"Debt-to-equity risk contribution {debt_score:.2f}/100",
            f"Current-ratio liquidity contribution {liquidity_score:.2f}/100",
            f"Drawdown risk contribution {drawdown_score:.2f}/100",
        ],
    )


def total_score(
    quality_score: float,
    valuation_score: float,
    technical_setup_score: float,
    risk_score: float,
) -> float:
    return clamp(
        (quality_score * 0.40)
        + (valuation_score * 0.25)
        + (technical_setup_score * 0.25)
        + (risk_score * 0.10)
    )
