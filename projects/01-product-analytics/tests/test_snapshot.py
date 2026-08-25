"""The failure this guards against is silent: a snapshot that differs from the
one the analysis was written against still loads, still runs, and produces
numbers that cannot be compared to anything already written down."""

from pathlib import Path

import pytest
from snapshot import (
    SESSION_SCHEMA,
    ChecksumMismatch,
    ContractViolation,
    checksum_path,
    load,
    measure,
    sha256_of,
    validate,
    verify,
    write_checksum,
)

HEADER = ",".join(SESSION_SCHEMA)
ROW_BOUGHT = (
    "ua,1001,2020-11-01,1604188800000000,12,"
    "true,true,true,true,true,1,true,true,"
    "desktop,Chrome,organic,google"
)
ROW_BROWSED = (
    "ub,1002,2020-11-02,1604275200000000,3,"
    "true,false,false,false,false,0,true,false,"
    "mobile,Safari,(none),(direct)"
)


@pytest.fixture
def snapshot(tmp_path: Path) -> Path:
    path = tmp_path / "sessions.csv"
    path.write_text(f"{HEADER}\n{ROW_BOUGHT}\n{ROW_BROWSED}\n")
    write_checksum(path)
    return path


def test_hash_is_stable_and_content_dependent(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_bytes(b"same")
    b.write_bytes(b"same")
    assert sha256_of(a) == sha256_of(b)

    b.write_bytes(b"different")
    assert sha256_of(a) != sha256_of(b)


def test_checksum_sits_next_to_the_snapshot(snapshot: Path) -> None:
    assert checksum_path(snapshot).name == "sessions.csv.sha256"
    assert checksum_path(snapshot).exists()


def test_verify_accepts_an_untouched_snapshot(snapshot: Path) -> None:
    assert verify(snapshot) == sha256_of(snapshot)


def test_verify_rejects_a_changed_snapshot(snapshot: Path) -> None:
    # One row appended: the kind of drift a revised public dataset produces.
    with open(snapshot, "a") as handle:
        handle.write(f"{ROW_BROWSED}\n")

    with pytest.raises(ChecksumMismatch, match="does not match its pin"):
        verify(snapshot)


def test_verify_refuses_when_there_is_no_pin(tmp_path: Path) -> None:
    unpinned = tmp_path / "sessions.csv"
    unpinned.write_text(f"{HEADER}\n{ROW_BOUGHT}\n")

    # Absent pin must not be treated as "nothing to check against".
    with pytest.raises(FileNotFoundError, match="No checksum"):
        verify(unpinned)


def test_load_applies_the_declared_schema(snapshot: Path) -> None:
    con = load(snapshot)
    types = dict(
        con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'sessions'"
        ).fetchall()
    )
    assert types == SESSION_SCHEMA


def test_load_reads_every_row(snapshot: Path) -> None:
    con = load(snapshot)
    assert con.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert (
        con.execute("SELECT count(*) FROM sessions WHERE purchased").fetchone()[0] == 1
    )


def test_load_rejects_a_table_name_that_is_not_an_identifier(snapshot: Path) -> None:
    # The table name reaches SQL by interpolation; anything but a bare identifier
    # must be refused before it gets there.
    with pytest.raises(ValueError, match="plain identifier"):
        load(snapshot, table="sessions; DROP TABLE sessions")


def test_load_refuses_a_snapshot_that_fails_its_pin(snapshot: Path) -> None:
    with open(snapshot, "a") as handle:
        handle.write(f"{ROW_BOUGHT}\n")

    with pytest.raises(ChecksumMismatch):
        load(snapshot)


# --- Data contract ---------------------------------------------------------
# Two identifiers, one of which buys in one of its two sessions.
ROW_SECOND_VISIT = (
    "ua,1003,2020-11-05,1604534400000000,4,"
    "true,false,false,false,false,0,true,false,"
    "desktop,Chrome,organic,google"
)
TINY_CONTRACT = {
    "distinct_users": 2,
    "purchase_sessions": 1,
    "purchasing_users": 1,
}


@pytest.fixture
def three_row_snapshot(tmp_path: Path) -> Path:
    path = tmp_path / "sessions.csv"
    path.write_text(f"{HEADER}\n{ROW_BOUGHT}\n{ROW_BROWSED}\n{ROW_SECOND_VISIT}\n")
    write_checksum(path)
    return path


def test_measure_recomputes_the_aggregates(three_row_snapshot: Path) -> None:
    got = measure(load(three_row_snapshot))
    assert got["distinct_users"] == 2
    assert got["purchase_sessions"] == 1
    assert got["purchasing_users"] == 1
    # ua has two sessions, ub has one.
    assert got["single_session_share"] == pytest.approx(0.5)


def test_validate_passes_a_matching_snapshot(three_row_snapshot: Path) -> None:
    validate(
        load(three_row_snapshot),
        contract=TINY_CONTRACT,
        single_session_share=0.5,
    )


def test_validate_catches_a_truncated_snapshot(tmp_path: Path) -> None:
    # The failure this exists for: a short export hashes fine and loads fine.
    truncated = tmp_path / "sessions.csv"
    truncated.write_text(f"{HEADER}\n{ROW_BOUGHT}\n")
    write_checksum(truncated)

    with pytest.raises(ContractViolation, match="distinct_users"):
        validate(load(truncated), contract=TINY_CONTRACT, single_session_share=0.5)


def test_validate_reports_every_mismatch_at_once(tmp_path: Path) -> None:
    empty = tmp_path / "sessions.csv"
    empty.write_text(f"{HEADER}\n{ROW_BROWSED}\n")
    write_checksum(empty)

    with pytest.raises(ContractViolation) as excinfo:
        validate(load(empty), contract=TINY_CONTRACT, single_session_share=0.5)

    # One re-export should fix all of them, so all of them are shown.
    message = str(excinfo.value)
    assert "distinct_users" in message
    assert "purchase_sessions" in message
    assert "single_session_share" in message
