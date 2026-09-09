"""M1 assertions: does the built population match what M0 froze?

Two layers. The logic is tested against a synthetic `loans` table small enough to
count by hand, which runs everywhere. The real population is then checked against
recorded figures, and skipped when the Lending Club extract is not on disk --
that file is 374MB and deliberately absent from the repository.

A filter that is subtly wrong still produces a plausible population. The only
defence is knowing the answer in advance.
"""

from __future__ import annotations

import duckdb
import pytest
from development_population import (
    BAD_STATUS,
    GOOD_STATUS,
    MATURITY_CUTOFF,
    TERM_MONTHS,
    build,
    fingerprint,
    summary,
)
from population import DB

# Recorded when the population was first built. A change here is either a bug or
# a decision -- never a silent drift.
EXPECTED = {
    "n": 641_116,
    "bads": 89_188,
    "goods": 551_928,
    "fingerprint": "fa9fa5f22eac50b1c7245f9be75b3972",
}

# id, issue, term, off_policy, status, months_past_term, why
FIXTURE_ROWS = [
    ("keep_bad", "2014-01-01", 36, False, BAD_STATUS, 5, "kept, target 1"),
    ("keep_good", "2014-02-01", 36, False, GOOD_STATUS, 5, "kept, target 0"),
    ("keep_edge", "2014-03-01", 36, False, GOOD_STATUS, 3, "kept, exactly at cutoff"),
    ("drop_term", "2014-01-01", 60, False, BAD_STATUS, 5, "60-month product"),
    ("drop_policy", "2009-01-01", 36, True, BAD_STATUS, 90, "off-policy"),
    (
        "drop_young",
        "2016-06-01",
        36,
        False,
        GOOD_STATUS,
        2,
        "one month short of cutoff",
    ),
    ("drop_current", "2014-04-01", 36, False, "Current", 5, "no terminal outcome"),
    (
        "drop_late",
        "2014-05-01",
        36,
        False,
        "Late (31-120 days)",
        5,
        "no terminal outcome",
    ),
    ("drop_null", None, 36, False, GOOD_STATUS, 5, "no issue date"),
]


@pytest.fixture
def con() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute("""
        CREATE TABLE loans (
            loan_id VARCHAR, issue_date DATE, term_months INTEGER,
            off_policy BOOLEAN, status VARCHAR, months_past_term INTEGER
        )
    """)
    connection.executemany(
        "INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?)",
        [row[:6] for row in FIXTURE_ROWS],
    )
    return build(connection)


# --- the logic, on numbers countable by hand ------------------------------


def test_only_the_three_intended_rows_survive(con) -> None:
    got = {r[0] for r in con.execute("SELECT loan_id FROM development").fetchall()}
    assert got == {"keep_bad", "keep_good", "keep_edge"}


def test_the_cutoff_is_inclusive(con) -> None:
    # A loan exactly at the cutoff is in; one month short is out. Off-by-one here
    # would silently shift the population by a whole vintage.
    surviving = {
        r[0] for r in con.execute("SELECT loan_id FROM development").fetchall()
    }
    assert "keep_edge" in surviving
    assert "drop_young" not in surviving


def test_target_maps_in_both_directions(con) -> None:
    # Domain alone (y in {0,1}) would pass even if every status mapped to 1.
    rows = con.execute("SELECT status, target FROM development").fetchall()
    assert {(BAD_STATUS, 1), (GOOD_STATUS, 0)} == set(rows)
    assert all(t in (0, 1) for _, t in rows)


def test_no_status_outside_the_two_terminal_ones(con) -> None:
    statuses = {
        r[0] for r in con.execute("SELECT DISTINCT status FROM development").fetchall()
    }
    assert statuses <= {BAD_STATUS, GOOD_STATUS}


def test_every_row_is_thirty_six_months_and_policy_compliant(con) -> None:
    assert (
        con.execute(
            f"SELECT count(*) FROM development WHERE term_months <> {TERM_MONTHS}"
        ).fetchone()[0]
        == 0
    )
    assert (
        con.execute(
            "SELECT count(*) FROM development WHERE months_past_term < ?",
            [MATURITY_CUTOFF],
        ).fetchone()[0]
        == 0
    )


def test_no_nulls_in_the_columns_the_target_depends_on(con) -> None:
    nulls = con.execute("""
        SELECT count(*) FROM development
        WHERE loan_id IS NULL OR issue_date IS NULL OR target IS NULL
    """).fetchone()[0]
    assert nulls == 0


def test_loan_ids_are_unique(con) -> None:
    n, distinct = con.execute(
        "SELECT count(*), count(DISTINCT loan_id) FROM development"
    ).fetchone()
    assert n == distinct


def test_lineage_accounts_for_every_dropped_row(con) -> None:
    steps = con.execute(
        "SELECT step, rows_in, rows_out FROM lineage ORDER BY rowid"
    ).df()
    # Each step's input is the previous step's output: no row vanishes unrecorded.
    pairs = zip(steps.itertuples(), steps.iloc[1:].itertuples(), strict=False)
    for previous, current in pairs:
        assert current.rows_in == previous.rows_out
    assert (
        steps.iloc[-1].rows_out
        == con.execute("SELECT count(*) FROM development").fetchone()[0]
    )


def test_vintage_profile_reconciles_with_the_population(con) -> None:
    n, bads = con.execute("SELECT sum(n), sum(bads) FROM vintage_profile").fetchone()
    assert (n, bads) == con.execute(
        "SELECT count(*), sum(target) FROM development"
    ).fetchone()


def test_fingerprint_ignores_row_order(con) -> None:
    before = fingerprint(con)
    con.execute(
        "CREATE OR REPLACE TABLE development AS "
        "SELECT * FROM development ORDER BY random()"
    )
    assert fingerprint(con) == before


# --- the real population --------------------------------------------------


@pytest.mark.skipif(not DB.exists(), reason="Lending Club extract not present")
def test_real_population_matches_the_recorded_figures() -> None:
    got = summary(build(duckdb.connect(str(DB))))
    assert {k: got[k] for k in EXPECTED} == EXPECTED
    assert str(got["first_issue"]) == "2007-06-01"
    assert str(got["last_issue"]) == "2016-01-01"
