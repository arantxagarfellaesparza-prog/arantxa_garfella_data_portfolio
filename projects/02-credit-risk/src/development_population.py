"""M1 — build the development population and the target.

Translates the decisions frozen in M0 (DECISIONS 003 and 004) into rows and a
label. It does **not** choose features: that is M2, and this module deliberately
carries no candidate predictors so nothing downstream can mistake a convenience
subset for a decision that has not been made.

What it produces:

* `development` — one row per loan: identifier, vintage, target, and the fields
  the filters acted on, so any assertion can be re-derived from the table itself.
* `lineage` — the filter waterfall with counts in and out at every step. A
  population you cannot reconstruct is a population you cannot defend.
* `vintage_profile` — per-vintage counts, event rate and date coverage.

The last one exists because the development population is not one population.
Median FICO moved from 705 to 685 and median DTI from 9.9 to 17.9 across the
window, so collapsing it to a single aggregate profile would make any later
statement about domain of applicability decorative. Historical development
support and operational applicability are different claims, and only the second
needs a recent reference window -- which is fixed during temporal validation,
not here.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pandas as pd

# Frozen in M0. Changing any of these changes the estimand, so they live here as
# named constants rather than inline in a query.
TERM_MONTHS = 36
MATURITY_CUTOFF = 3  # months past contractual term (DECISIONS 004)
BAD_STATUS = "Charged Off"
GOOD_STATUS = "Fully Paid"


@dataclass(frozen=True)
class Step:
    name: str
    reason: str
    predicate: str


# Order matters only for the counts, not for the result: the predicates are
# conjunctive. It is written to read as the argument, from widest to narrowest.
WATERFALL: tuple[Step, ...] = (
    Step(
        "parseable",
        "issue date, term and status must exist to define maturity or target",
        "issue_date IS NOT NULL AND term_months IS NOT NULL AND status IS NOT NULL",
    ),
    Step(
        "term_36m",
        "60-month loans are a different product (DECISIONS 003)",
        f"term_months = {TERM_MONTHS}",
    ),
    Step(
        "policy_compliant",
        "off-policy loans default at twice the rate and vanish after 2010",
        "NOT off_policy",
    ),
    Step(
        "mature",
        f"at least {MATURITY_CUTOFF} months past contractual term (DECISIONS 004)",
        f"months_past_term >= {MATURITY_CUTOFF}",
    ),
    Step(
        "terminal_outcome",
        "only Charged Off and Fully Paid map to the target",
        f"status IN ('{BAD_STATUS}', '{GOOD_STATUS}')",
    ),
)


def build(con: duckdb.DuckDBPyConnection | None = None) -> duckdb.DuckDBPyConnection:
    """Materialise `development`, `lineage` and `vintage_profile`."""
    con = con or connect_writable()

    lineage = []
    survivors = "loans"
    rows_in = con.execute("SELECT count(*) FROM loans").fetchone()[0]
    lineage.append(
        {
            "step": "raw",
            "reason": "accepted loans as materialised from the source file",
            "rows_in": rows_in,
            "rows_out": rows_in,
            "dropped": 0,
        }
    )

    predicates: list[str] = []
    for step in WATERFALL:
        predicates.append(step.predicate)
        where = " AND ".join(f"({p})" for p in predicates)
        rows_out = con.execute(
            f"SELECT count(*) FROM {survivors} WHERE {where}"
        ).fetchone()[0]
        lineage.append(
            {
                "step": step.name,
                "reason": step.reason,
                "rows_in": rows_in,
                "rows_out": rows_out,
                "dropped": rows_in - rows_out,
            }
        )
        rows_in = rows_out

    where = " AND ".join(f"({s.predicate})" for s in WATERFALL)
    con.execute(f"""
        CREATE OR REPLACE TABLE development AS
        SELECT
            loan_id,
            issue_date,
            date_trunc('month', issue_date)::DATE AS vintage_month,
            year(issue_date)                      AS vintage_year,
            term_months,
            months_past_term,
            status,
            -- The target is explicit rather than a cast of a boolean, so the
            -- mapping is visible in the table and testable in both directions.
            CASE status
                WHEN '{BAD_STATUS}'  THEN 1
                WHEN '{GOOD_STATUS}' THEN 0
            END AS target
        FROM loans
        WHERE {where}
    """)

    # Registered so DuckDB's replacement scan can read it by name.
    lineage_df = pd.DataFrame(lineage)  # noqa: F841 - referenced by the query below
    con.execute("CREATE OR REPLACE TABLE lineage AS SELECT * FROM lineage_df")
    con.execute("""
        CREATE OR REPLACE TABLE vintage_profile AS
        SELECT
            vintage_year,
            count(*)                                          AS n,
            sum(target)                                       AS bads,
            count(*) - sum(target)                            AS goods,
            round(100.0 * sum(target) / count(*), 4)          AS event_rate_pct,
            min(issue_date)                                   AS first_issue,
            max(issue_date)                                   AS last_issue,
            count(DISTINCT vintage_month)                     AS months_covered
        FROM development
        GROUP BY vintage_year
        ORDER BY vintage_year
    """)
    return con


def connect_writable() -> duckdb.DuckDBPyConnection:
    """The audit connection is read-only; M1 needs to write its own tables."""
    from population import DB
    from population import build as build_audit

    build_audit()
    return duckdb.connect(str(DB))


def fingerprint(con: duckdb.DuckDBPyConnection) -> str:
    """An order-independent hash of (loan_id, target).

    Order-independent on purpose: a fingerprint that changes when a query adds an
    ORDER BY fails for no reason, and a check that cries wolf gets ignored.
    """
    return con.execute("""
        SELECT md5(string_agg(row_hash, '' ORDER BY row_hash))
        FROM (SELECT md5(loan_id || ':' || target) AS row_hash FROM development)
    """).fetchone()[0]


def summary(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    n, bads, first, last = con.execute("""
        SELECT count(*), sum(target), min(issue_date), max(issue_date) FROM development
    """).fetchone()
    return {
        "n": n,
        "bads": bads,
        "goods": n - bads,
        "event_rate_pct": round(100.0 * bads / n, 4),
        "first_issue": first,
        "last_issue": last,
        "fingerprint": fingerprint(con),
    }
