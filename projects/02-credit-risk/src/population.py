"""Materialise the loan-level table once, so the audit does not reparse 374MB
of gzipped CSV on every query.

Only columns needed for M0 and the leakage audit that follows are read. Nothing
is filtered here beyond unparseable rows: population decisions belong in
DECISIONS.md, not hidden inside a loader.

Snapshot is derived rather than assumed. The file is named for the last issuance
quarter (2018Q4) but observation runs to 2019-04, which is four months of extra
maturity that a hardcoded cutoff would have thrown away.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

DATA = Path(__file__).parents[1] / "data"
ACCEPTED = DATA / "raw" / "accepted_2007_to_2018Q4.csv.gz"
DB = DATA / "interim" / "lc.duckdb"

# Origination-time candidates only. Post-origination fields (payments,
# recoveries, hardship, settlement) are deliberately absent: they belong to the
# M2 leakage table, not to a working population.
BUILD = """
CREATE OR REPLACE TABLE loans AS
SELECT
    strptime(issue_d, '%b-%Y')::DATE                                     AS issue_date,
    CASE WHEN term LIKE '%36%' THEN 36 WHEN term LIKE '%60%' THEN 60 END AS term_months,
    loan_status LIKE 'Does not meet%'                                    AS off_policy,
    replace(loan_status, 'Does not meet the credit policy. Status:', '') AS status,
    grade,
    sub_grade,
    TRY_CAST(int_rate    AS DOUBLE)  AS int_rate,
    TRY_CAST(loan_amnt   AS DOUBLE)  AS loan_amnt,
    TRY_CAST(annual_inc  AS DOUBLE)  AS annual_inc,
    TRY_CAST(dti         AS DOUBLE)  AS dti,
    TRY_CAST(fico_range_low  AS DOUBLE) AS fico_low,
    TRY_CAST(fico_range_high AS DOUBLE) AS fico_high,
    TRY_CAST(revol_util  AS DOUBLE)  AS revol_util,
    TRY_CAST(delinq_2yrs AS DOUBLE)  AS delinq_2yrs,
    TRY_CAST(inq_last_6mths AS DOUBLE) AS inq_6m,
    TRY_CAST(open_acc    AS DOUBLE)  AS open_acc,
    TRY_CAST(pub_rec     AS DOUBLE)  AS pub_rec,
    TRY_CAST(total_acc   AS DOUBLE)  AS total_acc,
    emp_length,
    home_ownership,
    purpose,
    verification_status,
    addr_state,
    date_diff('month', strptime(earliest_cr_line, '%b-%Y')::DATE,
                       strptime(issue_d, '%b-%Y')::DATE)                 AS credit_hist_months,
    date_diff('month', strptime(issue_d, '%b-%Y')::DATE, DATE '2019-04-01') AS age_months
FROM read_csv(?, header = true, all_varchar = true)
WHERE issue_d IS NOT NULL AND term IS NOT NULL AND loan_status IS NOT NULL
"""


def build(force: bool = False) -> Path:
    """Create the local database if it is not already there."""
    if DB.exists() and not force:
        return DB
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute(BUILD, [str(ACCEPTED)])
    con.execute("ALTER TABLE loans ADD COLUMN months_past_term INTEGER")
    con.execute("UPDATE loans SET months_past_term = age_months - term_months")
    con.close()
    return DB


def connect() -> duckdb.DuckDBPyConnection:
    build()
    return duckdb.connect(str(DB), read_only=True)


if __name__ == "__main__":
    path = build(force=True)
    con = duckdb.connect(str(path), read_only=True)
    n = con.execute("SELECT count(*) FROM loans").fetchone()[0]
    print(f"Built {path} with {n:,} loans")
