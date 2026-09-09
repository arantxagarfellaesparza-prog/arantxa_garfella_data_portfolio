"""Step 1 of M0: confirm what the files actually contain.

Written before the data was downloaded, deliberately without parsing anything.
The column names, the format of `issue_d` and the exact set of `loan_status`
values are all things this project has so far only assumed from a published data
dictionary. Assuming them into a parser is how an audit turns into a guess.

So this prints raw sample values and lets the next step be written against what
is really there.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

DATA = Path(__file__).parents[1] / "data" / "raw"
ACCEPTED = DATA / "accepted_2007_to_2018Q4.csv.gz"
REJECTED = DATA / "rejected_2007_to_2018Q4.csv.gz"

# Substrings that mark a column as carrying a date or an elapsed time. The second
# group matters as much as the first: `mths_since_last_delinq` is a bureau field
# measured at origination about the borrower's PRIOR history, not this loan's
# performance, and it is routinely mistaken for the latter.
DATE_HINTS = ("_d", "date", "_dt")
ELAPSED_HINTS = ("mths_since", "months_since", "mo_sin")


def columns(path: Path, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Column names and inferred types, without materialising the file."""
    return con.execute(
        f"DESCRIBE SELECT * FROM read_csv_auto('{path}', sample_size = 20000)"
    ).df()


def sample_values(
    path: Path, column: str, con: duckdb.DuckDBPyConnection, limit: int = 8
) -> list[str]:
    """Distinct raw values, as text. Never parsed here."""
    # Identifiers are quoted: the rejected file has column names with spaces
    # ("Application Date"), which parse as two tokens otherwise.
    quoted = '"' + column.replace('"', '""') + '"'
    rows = con.execute(
        f"SELECT DISTINCT CAST({quoted} AS VARCHAR) FROM read_csv_auto("
        f"'{path}', sample_size = 20000) WHERE {quoted} IS NOT NULL LIMIT {limit}"
    ).fetchall()
    return [r[0] for r in rows]


def main() -> int:
    missing = [p for p in (ACCEPTED, REJECTED) if not p.exists()]
    if missing:
        print("Missing files:")
        for path in missing:
            print(f"  {path}")
        print("\nDownload wordsforthewise/lending-club from Kaggle into data/raw/.")
        print("Do not decompress: DuckDB reads .csv.gz directly.")
        return 1

    con = duckdb.connect()

    for label, path in (("ACCEPTED", ACCEPTED), ("REJECTED", REJECTED)):
        schema = columns(path, con)
        names = schema["column_name"].tolist()
        print(f"\n{'=' * 72}\n{label}: {path.name}\n{'=' * 72}")
        print(f"{len(names)} columns")

        dated = [c for c in names if any(h in c.lower() for h in DATE_HINTS)]
        elapsed = [c for c in names if any(h in c.lower() for h in ELAPSED_HINTS)]

        print(f"\n-- Date-like columns ({len(dated)}) ------------------------")
        for c in dated:
            print(f"  {c:<28} {sample_values(path, c, con)}")

        print(f"\n-- Elapsed-time columns ({len(elapsed)}) -------------------")
        print("   Bureau fields about the borrower's history at origination,")
        print("   NOT this loan's performance. Listed so they cannot be confused.")
        for c in elapsed:
            print(f"  {c}")

    print(f"\n{'=' * 72}\nGate 1: is any of the above a first-delinquency,")
    print("default, or charge-off date for the loan itself?")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
