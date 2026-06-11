from __future__ import annotations

import argparse
from pathlib import Path

from packages.reports.markdown import write_markdown_report
from packages.screeners.quality_200dma import load_strategy_config, screen_us


def main() -> None:
    parser = argparse.ArgumentParser(description="Local-first investment research harness.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    screen_parser = subparsers.add_parser("screen-us", help="Run the US 200DMA quality screener.")
    screen_parser.add_argument("--config", "-c", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "screen-us":
        screen_us_command(args.config)


def screen_us_command(config: Path) -> None:
    """Run the US 200DMA quality screener and write evidence JSON for every ticker."""
    strategy_config = load_strategy_config(config)
    results = screen_us(strategy_config)
    report_path = write_markdown_report(results, strategy_config.report_path)
    headers = [
        "Rank",
        "Ticker",
        "Signal",
        "Total",
        "Quality",
        "Valuation",
        "Technical",
        "Risk",
        "Risk flags",
    ]
    print(" | ".join(headers))
    print(" | ".join("-" * len(header) for header in headers))
    for result in results:
        print(
            " | ".join(
                [
                    str(result.rank),
                    result.ticker,
                    result.signal.value,
                    f"{result.total_score:.2f}",
                    f"{result.quality_score:.2f}",
                    f"{result.valuation_score:.2f}",
                    f"{result.technical_setup_score:.2f}",
                    f"{result.risk_score:.2f}",
                    ", ".join(result.risk_flags),
                ]
            )
        )
    print(f"Evidence written to {strategy_config.evidence_dir}")
    print(f"Markdown report written to {report_path}")


if __name__ == "__main__":
    main()
