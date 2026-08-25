"""Pin the exported snapshot and load it into DuckDB.

Reproducibility from a public dataset is only as stable as the dataset. The GA4
sample can be revised or withdrawn, and a silently different file would change
every number downstream while every script still ran. So the file is pinned by
checksum, the checksum is committed, and loading refuses to proceed on a
mismatch.

The schema is declared rather than sniffed for the same reason: type inference
reads the first N rows, so a column that is all-integer at the top of the file
and mixed further down can change type between runs or DuckDB versions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb

# Mirrors the SELECT list of extract_sessions.sql, in order. If that query
# changes, this changes with it in the same commit.
SESSION_SCHEMA: dict[str, str] = {
    "user_pseudo_id": "VARCHAR",
    "ga_session_id": "BIGINT",
    "session_date": "DATE",
    "session_start_us": "BIGINT",
    "n_events": "BIGINT",
    "viewed_item": "BOOLEAN",
    "added_to_cart": "BOOLEAN",
    "began_checkout": "BOOLEAN",
    "added_payment_info": "BOOLEAN",
    "purchased": "BOOLEAN",
    "n_purchases": "BIGINT",
    "has_session_start": "BOOLEAN",
    "has_first_visit": "BOOLEAN",
    "device_category": "VARCHAR",
    "browser": "VARCHAR",
    "traffic_medium": "VARCHAR",
    "traffic_source": "VARCHAR",
}

_CHUNK = 1 << 20


class ChecksumMismatch(RuntimeError):
    """The snapshot on disk is not the one the analysis was written against."""


def sha256_of(path: Path | str) -> str:
    """Hash a file in chunks, so a multi-hundred-MB export does not need to fit
    in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_path(snapshot: Path | str) -> Path:
    return Path(snapshot).with_suffix(Path(snapshot).suffix + ".sha256")


def write_checksum(snapshot: Path | str) -> Path:
    """Record the pin. Run once, when the snapshot is first exported."""
    target = checksum_path(snapshot)
    target.write_text(f"{sha256_of(snapshot)}  {Path(snapshot).name}\n")
    return target


def verify(snapshot: Path | str) -> str:
    """Raise unless the file matches its committed checksum.

    Refusing to run is the point. A snapshot that quietly differs produces
    results that look fine and are not comparable to anything already written
    down.
    """
    snapshot = Path(snapshot)
    pin = checksum_path(snapshot)
    if not pin.exists():
        raise FileNotFoundError(
            f"No checksum at {pin}. Run write_checksum() once when the snapshot "
            "is first exported, and commit the .sha256 file."
        )

    expected = pin.read_text().split()[0]
    actual = sha256_of(snapshot)
    if actual != expected:
        raise ChecksumMismatch(
            f"{snapshot.name} does not match its pin.\n"
            f"  expected {expected}\n"
            f"  actual   {actual}\n"
            "The source may have been revised, or the export differed. Do not "
            "re-pin without establishing which."
        )
    return actual


def load(
    snapshot: Path | str,
    con: duckdb.DuckDBPyConnection | None = None,
    *,
    table: str = "sessions",
    check: bool = True,
) -> duckdb.DuckDBPyConnection:
    """Verify the snapshot and load it into DuckDB as `table`."""
    snapshot = Path(snapshot)
    if check:
        verify(snapshot)

    if not table.isidentifier():
        # `table` is interpolated into SQL because DuckDB will not parameterise an
        # identifier. It is always ours today, but a caller passing user input
        # should fail here rather than reach the parser.
        raise ValueError(f"table must be a plain identifier, got {table!r}")

    con = con or duckdb.connect()
    columns = ", ".join(f"'{name}': '{sql}'" for name, sql in SESSION_SCHEMA.items())
    con.execute(
        f"CREATE OR REPLACE TABLE {table} AS "
        f"SELECT * FROM read_csv(?, header = true, columns = {{{columns}}})",
        [str(snapshot)],
    )
    return con


# --- Data contract ---------------------------------------------------------
# A checksum pins a file; it does not say the file is right. A truncated or
# mangled export hashes perfectly well and then quietly changes every number
# downstream. These are aggregates measured against the full source in BigQuery
# before exporting, so the snapshot has something to be wrong against.
SNAPSHOT_CONTRACT: dict[str, int] = {
    "distinct_users": 270_154,
    "purchase_sessions": 4_848,
    "purchasing_users": 4_419,
}

# Share of identifiers with exactly one session. Held apart from the counts
# because it is compared with a tolerance rather than exactly.
SINGLE_SESSION_SHARE = 0.8247


class ContractViolation(RuntimeError):
    """The snapshot loaded, and it is not the dataset the analysis expects."""


def measure(
    con: duckdb.DuckDBPyConnection, *, table: str = "sessions"
) -> dict[str, float]:
    """Recompute the contract aggregates from a loaded snapshot."""
    if not table.isidentifier():
        raise ValueError(f"table must be a plain identifier, got {table!r}")

    counts = con.execute(f"""
        SELECT
          count(DISTINCT user_pseudo_id),
          count(*) FILTER (WHERE purchased),
          count(DISTINCT user_pseudo_id) FILTER (WHERE purchased)
        FROM {table}
    """).fetchone()

    share = con.execute(f"""
        WITH per_user AS (
          SELECT user_pseudo_id, count(*) AS sessions
          FROM {table} GROUP BY user_pseudo_id
        )
        SELECT count(*) FILTER (WHERE sessions = 1) / count(*) FROM per_user
    """).fetchone()[0]

    return {
        "distinct_users": counts[0],
        "purchase_sessions": counts[1],
        "purchasing_users": counts[2],
        "single_session_share": share,
    }


def validate(
    con: duckdb.DuckDBPyConnection,
    *,
    table: str = "sessions",
    contract: dict[str, int] | None = None,
    single_session_share: float | None = None,
    tolerance: float = 0.001,
) -> dict[str, float]:
    """Raise unless the snapshot reproduces the aggregates measured at source."""
    contract = SNAPSHOT_CONTRACT if contract is None else contract
    expected_share = (
        SINGLE_SESSION_SHARE if single_session_share is None else single_session_share
    )

    actual = measure(con, table=table)
    problems = [
        f"  {name}: expected {want:,}, got {actual[name]:,.0f}"
        for name, want in contract.items()
        if actual[name] != want
    ]

    if abs(actual["single_session_share"] - expected_share) > tolerance:
        problems.append(
            f"  single_session_share: expected {expected_share:.4f} "
            f"(±{tolerance}), got {actual['single_session_share']:.4f}"
        )

    if problems:
        raise ContractViolation(
            "Snapshot does not match the aggregates measured at source:\n"
            + "\n".join(problems)
            + "\nA truncated or mangled export produces exactly this. Re-export "
            "rather than adjusting the contract."
        )
    return actual


def _main() -> int:
    """Validate a snapshot, and pin it only once it has passed.

    The order is the point: pinning first would record the checksum of whatever
    happened to download, which is how a truncated export becomes the official
    dataset.
    """
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument(
        "--pin",
        action="store_true",
        help="write the .sha256 file after validation passes",
    )
    args = parser.parse_args()

    con = load(args.snapshot, check=False)
    try:
        measured = validate(con)
    except ContractViolation as exc:
        print(exc)
        return 1

    for name, value in measured.items():
        print(
            f"  {name:>22}: {value:,.4f}"
            if isinstance(value, float)
            else f"  {name:>22}: {value:,}"
        )

    if args.pin:
        print(f"\nPinned: {write_checksum(args.snapshot)}")
    else:
        print("\nContract passed. Re-run with --pin to record the checksum.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
