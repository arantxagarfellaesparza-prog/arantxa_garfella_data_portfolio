"""Run the project's SQL against the pinned snapshot.

The queries live in .sql files rather than in Python strings so they can be read,
diffed and reviewed as SQL. This module only loads data and executes them.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
from levers import BaseRates, sensitivity
from snapshot import load, validate

SQL_DIR = Path(__file__).parent
DEFAULT_SNAPSHOT = Path(__file__).parents[1] / "data" / "raw" / "ga4_sessions.csv"


def open_snapshot(
    snapshot: Path | str = DEFAULT_SNAPSHOT, *, check_contract: bool = True
) -> duckdb.DuckDBPyConnection:
    """Load the pinned snapshot, verifying both its checksum and its contents."""
    con = load(snapshot)
    if check_contract:
        validate(con)
    return con


def run(name: str, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Execute `<name>.sql` from this directory and return the result."""
    query = (SQL_DIR / f"{name}.sql").read_text()
    return con.execute(query).df()


def base_rates(con: duckdb.DuckDBPyConnection) -> BaseRates:
    """Read the measured rates the lever comparison is built on."""
    row = run("base_rates", con).iloc[0]
    return BaseRates(
        sessions=int(row.sessions),
        identifiers=int(row.identifiers),
        p_view=float(row.p_view),
        p_buy_given_view=float(row.p_buy_given_view),
        p_return=float(row.p_return),
        p_buy_after_return=float(row.p_buy_after_return),
    )


def _main() -> int:
    con = open_snapshot()
    for name in ("reconciliation", "funnel", "nesting"):
        print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
        print(run(name, con).to_string(index=False))

    rates = base_rates(con)
    print(f"\n{'=' * 70}\nlever sensitivity\n{'=' * 70}")
    print(f"baseline purchases implied by decomposition: {rates.purchases:,.0f}")
    print(sensitivity(rates).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
