"""The funnel is tested against a fixture small enough to count by hand.

A funnel query that is subtly wrong still returns plausible percentages, so the
only way to know it is right is to know the answer in advance.
"""

from pathlib import Path

import duckdb
import pytest
from analysis import run
from snapshot import SESSION_SCHEMA

HEADER = ",".join(SESSION_SCHEMA)


def session(
    user: str,
    sid: int,
    *,
    viewed: bool = False,
    carted: bool = False,
    checkout: bool = False,
    payment: bool = False,
    bought: bool = False,
) -> str:
    flags = ",".join(
        str(b).lower() for b in (viewed, carted, checkout, payment, bought)
    )
    return (
        f"{user},{sid},2020-11-01,1604188800000000,5,{flags},"
        f"{1 if bought else 0},true,false,desktop,Chrome,organic,google"
    )


# Eight sessions, six of them viewers, designed so every number below is
# countable by hand:
#   viewers          6
#   carted           3   (one of them never viewed -- excluded from the funnel)
#   checkout         3
#   payment          2
#   purchased        2   (one purchase never carted: the DECISIONS 004 defect)
ROWS = [
    session("a", 1, viewed=True, carted=True, checkout=True, payment=True, bought=True),
    session("a", 2, viewed=True),
    session("b", 1, viewed=True, carted=True, checkout=True),
    session("c", 1, viewed=True, checkout=True, payment=True, bought=True),
    session("d", 1, viewed=True),
    session("e", 1, viewed=True),
    session("f", 1),
    session("g", 1, carted=True),
]


@pytest.fixture
def con(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    csv = tmp_path / "sessions.csv"
    csv.write_text(HEADER + "\n" + "\n".join(ROWS) + "\n")
    columns = ", ".join(f"'{n}': '{t}'" for n, t in SESSION_SCHEMA.items())
    connection = duckdb.connect()
    connection.execute(
        f"CREATE TABLE sessions AS SELECT * FROM read_csv(?, header = true, "
        f"columns = {{{columns}}})",
        [str(csv)],
    )
    return connection


def test_funnel_counts_are_the_hand_computed_ones(con) -> None:
    got = run("funnel", con).set_index("step")["sessions"].to_dict()
    assert got == {
        "view_item": 6,
        "add_to_cart": 2,  # 'g' carted but never viewed, so it is not in the funnel
        "begin_checkout": 3,
        "add_payment_info": 2,
        "purchase": 2,
    }


def test_funnel_percentages_are_relative_to_viewers(con) -> None:
    df = run("funnel", con).set_index("step")
    assert df.loc["view_item", "pct_of_viewers"] == 100.0
    assert df.loc["purchase", "pct_of_viewers"] == pytest.approx(33.33, abs=0.01)
    # Step-to-step: 2 payments from 3 checkouts.
    assert df.loc["add_payment_info", "pct_of_previous"] == pytest.approx(
        66.67, abs=0.01
    )


def test_funnel_is_not_nested_and_says_so(con) -> None:
    # add_to_cart (2) is below begin_checkout (3): impossible in a real funnel,
    # and exactly the defect DECISIONS 004 records.
    df = run("funnel", con).set_index("step")
    assert df.loc["add_to_cart", "sessions"] < df.loc["begin_checkout", "sessions"]


def test_reconciliation_separates_the_two_grains(con) -> None:
    df = run("reconciliation", con).set_index("grain")

    # 8 sessions, 2 of which purchase.
    assert df.loc["sessions", "total"] == 8
    assert df.loc["sessions", "pct_converting_overall"] == pytest.approx(25.0)

    # 7 identifiers ('a' has two sessions), 2 of which purchase. The identifier
    # rate is the higher one, which is the point of reporting both.
    assert df.loc["identifiers", "total"] == 7
    assert df.loc["identifiers", "pct_converting_overall"] == pytest.approx(
        28.57, abs=0.01
    )


def test_nesting_violations_are_counted(con) -> None:
    got = run("nesting", con).set_index("violation")["sessions"].to_dict()
    assert got["purchased without add_to_cart"] == 1  # session 'c'
    assert got["purchased without begin_checkout"] == 0
    assert got["checkout without add_to_cart"] == 1  # session 'c'


def test_segments_split_first_from_return_visits(con) -> None:
    df = run("segments", con).set_index("segment")

    # Seven identifiers, so seven first visits; 'a' is the only one with a
    # second, so one return visit. They must add back to the eight sessions.
    assert df.loc["1_first_visit", "sessions"] == 7
    assert df.loc["2_return_visit", "sessions"] == 1
    assert df["sessions"].sum() == 8


def test_segments_rank_sessions_by_time_not_by_id(con) -> None:
    # 'a' bought in its earlier session, so the purchase belongs to the first
    # visit. Getting the ordering backwards would silently move every purchase
    # into the wrong segment and invert the headline result.
    df = run("segments", con).set_index("segment")
    assert df.loc["1_first_visit", "pct_purchasing"] > 0
    assert df.loc["2_return_visit", "pct_purchasing"] == 0
