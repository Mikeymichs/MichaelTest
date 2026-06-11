from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from packages.data.models import CompanyProfile, Fundamentals
from packages.data.providers import PriceRows


class DuckDBCache:
    """Local cache layer with a DuckDB-compatible role and SQLite fallback storage.

    The class boundary is intentionally isolated so a production deployment can
    swap the internals to native DuckDB without changing providers or screeners.
    The current implementation is dependency-light for offline test environments.
    """

    def __init__(self, path: Path | str = "research/cache.duckdb") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path))
        self._connection.row_factory = sqlite3.Row
        self._create_tables()

    def close(self) -> None:
        self._connection.close()

    def _create_tables(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                ticker TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, date)
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS fundamentals (
                ticker TEXT PRIMARY KEY,
                revenue_growth REAL,
                gross_margin REAL,
                operating_margin REAL,
                free_cash_flow_margin REAL,
                return_on_equity REAL,
                debt_to_equity REAL,
                current_ratio REAL,
                pe_ratio REAL,
                forward_pe REAL,
                price_to_sales REAL,
                ev_to_ebitda REAL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS company_profiles (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                sector TEXT,
                industry TEXT,
                exchange TEXT,
                currency TEXT
            )
            """
        )
        self._connection.commit()

    def get_price_history(self, ticker: str, start: date, end: date) -> PriceRows:
        rows = self._connection.execute(
            """
            SELECT date, open, high, low, close, volume
            FROM price_history
            WHERE ticker = ? AND date BETWEEN ? AND ?
            ORDER BY date
            """,
            [ticker.upper(), start.isoformat(), end.isoformat()],
        ).fetchall()
        return [
            {
                "date": date.fromisoformat(row["date"]),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }
            for row in rows
        ]

    def put_price_history(self, ticker: str, prices: PriceRows) -> None:
        if not prices:
            return
        self._connection.executemany(
            "INSERT OR REPLACE INTO price_history VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    ticker.upper(),
                    row["date"].isoformat(),
                    row["open"],
                    row["high"],
                    row["low"],
                    row["close"],
                    row["volume"],
                )
                for row in prices
            ],
        )
        self._connection.commit()

    def get_fundamentals(self, ticker: str) -> Fundamentals | None:
        row = self._connection.execute(
            "SELECT * FROM fundamentals WHERE ticker = ?", [ticker.upper()]
        ).fetchone()
        return None if row is None else Fundamentals.model_validate(dict(row))

    def put_fundamentals(self, fundamentals: Fundamentals) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO fundamentals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            list(fundamentals.model_dump().values()),
        )
        self._connection.commit()

    def get_company_profile(self, ticker: str) -> CompanyProfile | None:
        row = self._connection.execute(
            "SELECT * FROM company_profiles WHERE ticker = ?", [ticker.upper()]
        ).fetchone()
        return None if row is None else CompanyProfile.model_validate(dict(row))

    def put_company_profile(self, profile: CompanyProfile) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO company_profiles VALUES (?, ?, ?, ?, ?, ?)",
            list(profile.model_dump().values()),
        )
        self._connection.commit()
