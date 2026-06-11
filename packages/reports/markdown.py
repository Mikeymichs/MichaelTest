from __future__ import annotations

from pathlib import Path

from packages.screeners.models import ScreenerResult


def write_markdown_report(results: list[ScreenerResult], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 200DMA Quality Screener Report",
        "",
        (
            "This report is generated from deterministic scores. "
            "It is research only, not a trade order."
        ),
        "",
        "| Rank | Ticker | Signal | Total | Quality | Valuation | Technical | Risk | Risk flags |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            "| {rank} | {ticker} | {signal} | {total:.2f} | {quality:.2f} | {valuation:.2f} "
            "| {technical:.2f} | {risk:.2f} | {flags} |".format(
                rank=result.rank,
                ticker=result.ticker,
                signal=result.signal.value,
                total=result.total_score,
                quality=result.quality_score,
                valuation=result.valuation_score,
                technical=result.technical_setup_score,
                risk=result.risk_score,
                flags=", ".join(result.risk_flags),
            )
        )
    lines.extend(["", "## Evidence files", ""])
    for result in results:
        lines.append(f"- {result.ticker}: `{result.evidence_file}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
