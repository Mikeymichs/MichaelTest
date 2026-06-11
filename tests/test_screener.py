from __future__ import annotations

import json
from pathlib import Path

from packages.data.providers import MockMarketDataProvider
from packages.screeners.models import StrategyConfig
from packages.screeners.quality_200dma import screen_us


def test_screen_us_writes_evidence_for_default_five_tickers(tmp_path: Path) -> None:
    config = StrategyConfig(
        tickers=["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"],
        start="2024-01-01",
        end="2025-06-30",
        provider="mock",
        cache_path=tmp_path / "cache.duckdb",
        evidence_dir=tmp_path / "evidence",
        report_path=tmp_path / "report.md",
    )
    results = screen_us(config, provider=MockMarketDataProvider())
    assert len(results) == 5
    assert [result.rank for result in results] == [1, 2, 3, 4, 5]
    for result in results:
        assert result.evidence_file is not None
        assert result.evidence_file.exists()
        payload = json.loads(result.evidence_file.read_text(encoding="utf-8"))
        assert payload["ticker"] == result.ticker
        assert payload["signal"] in {"BUY_RESEARCH", "WATCHLIST", "AVOID", "INSUFFICIENT_DATA"}
        assert "quality" in payload["scoring_explanation"]
