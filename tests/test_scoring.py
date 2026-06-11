from __future__ import annotations

from packages.data.models import Fundamentals
from packages.screeners.models import CandidateClass, TechnicalSnapshot
from packages.screeners.quality_200dma import classify_candidate, detect_risk_flags
from packages.screeners.scoring import (
    score_quality,
    score_risk,
    score_technical_setup,
    score_valuation,
    total_score,
)


def strong_fundamentals() -> Fundamentals:
    return Fundamentals(
        ticker="TEST",
        revenue_growth=0.18,
        gross_margin=0.62,
        operating_margin=0.28,
        free_cash_flow_margin=0.21,
        return_on_equity=0.30,
        debt_to_equity=0.30,
        current_ratio=1.8,
        pe_ratio=20.0,
        forward_pe=17.0,
        price_to_sales=4.0,
        ev_to_ebitda=12.0,
    )


def test_quality_score_is_deterministic_and_bounded() -> None:
    first = score_quality(strong_fundamentals())
    second = score_quality(strong_fundamentals())
    assert first == second
    assert 0 <= first.score <= 100
    assert first.score > 70
    assert len(first.explanation) == 5


def test_valuation_score_rewards_lower_multiples() -> None:
    attractive = score_valuation(strong_fundamentals())
    expensive = score_valuation(
        strong_fundamentals().model_copy(
            update={
                "pe_ratio": 55.0,
                "forward_pe": 40.0,
                "price_to_sales": 18.0,
                "ev_to_ebitda": 35.0,
            }
        )
    )
    assert attractive.score > expensive.score
    assert 0 <= expensive.score <= 100


def test_technical_setup_scores_near_sma_with_positive_momentum() -> None:
    result = score_technical_setup(
        distance_to_sma200=-0.03,
        drawdown_52w=-0.10,
        momentum_6m=0.08,
        momentum_12m=0.16,
    )
    assert result.score > 60
    assert len(result.explanation) == 4


def test_risk_score_penalizes_leverage_and_liquidity() -> None:
    safe = score_risk(strong_fundamentals(), drawdown_52w=-0.08)
    risky = score_risk(
        strong_fundamentals().model_copy(update={"debt_to_equity": 3.0, "current_ratio": 0.5}),
        drawdown_52w=-0.40,
    )
    assert safe.score > risky.score
    assert risky.score < 35


def test_total_score_uses_required_weights() -> None:
    assert total_score(80, 60, 70, 50) == 69.5


def test_candidate_classification() -> None:
    assert classify_candidate(80, 65, 70, 75, ["none"]) == CandidateClass.BUY_RESEARCH
    assert classify_candidate(80, 40, 70, 75, ["none"]) == CandidateClass.WATCHLIST
    assert classify_candidate(80, 65, 70, 75, ["high_leverage"]) == CandidateClass.AVOID


def test_risk_flag_detection() -> None:
    flags = detect_risk_flags(
        strong_fundamentals().model_copy(update={"debt_to_equity": 2.5, "current_ratio": 0.7}),
        TechnicalSnapshot(
            current_price=100,
            sma50=110,
            sma100=115,
            sma200=120,
            distance_to_sma200=-0.16,
            drawdown_52w=-0.42,
            momentum_6m=-0.10,
            momentum_12m=-0.20,
        ),
    )
    assert "high_leverage" in flags
    assert "poor_liquidity" in flags
    assert "deep_drawdown" in flags
