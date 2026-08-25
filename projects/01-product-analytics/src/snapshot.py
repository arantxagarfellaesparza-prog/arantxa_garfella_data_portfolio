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
