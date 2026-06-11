# investing-agent

A local-first investment research harness for deterministic investment screening. This project is **not** a live trading bot: it has no broker execution, no autonomous trades, and every recommendation emits auditable evidence JSON.

## Quick start

```bash
uv sync --extra dev
uv run investing-agent screen-us --config config/strategy.200dma-quality.yaml
uv run pytest
uv run ruff check .
uv run mypy .
```

The default strategy screens `AAPL`, `MSFT`, `NVDA`, `GOOGL`, and `AMZN` using deterministic mocked market data and fundamentals so the repository works locally without API credentials. Evidence is written to `research/evidence/` and a Markdown report is written to `research/reports/`.

## Architecture

- `packages/data`: market-data provider interface, yfinance starter adapter, OpenBB provider interface placeholder, and DuckDB cache.
- `packages/indicators`: SMA, momentum, distance-to-average, and drawdown calculations.
- `packages/screeners`: deterministic 200-day moving-average quality screener and scoring functions.
- `packages/reports`: Markdown report rendering.
- `apps/cli`: Typer CLI entrypoint.

## Safety constraints

- No broker execution code.
- No autonomous trading code.
- Deterministic scoring only; no LLM calls are used for scoring.
