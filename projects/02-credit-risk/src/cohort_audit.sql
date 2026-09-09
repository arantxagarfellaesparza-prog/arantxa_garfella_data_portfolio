-- M0 step 3: how complete is each cohort, as a function of its age?
--
-- `issue_d + term <= snapshot` does not imply a resolved cohort. Charge-off
-- follows the last payment by some months, so a loan that deteriorates near the
-- end of its term resolves after its contractual maturity. Maturity is therefore
-- measured rather than assumed.
--
-- The x-axis is months PAST contractual term, not calendar age. That makes the
-- 36- and 60-month books directly comparable: zero means "just reached term" for
-- both, and the shape of the tail is what the maturity cutoff has to be chosen
-- from.
--
-- Snapshot is derived from the data (max last_credit_pull_d = 2019-04), not from
-- the filename: the file is named for the last issuance quarter, and observation
-- runs four months beyond it.
--
-- Off-policy loans are counted apart rather than folded in. They are 0.12% of
-- the book overall but concentrate in the early vintages, which are exactly the
-- ones the macro question needs.

WITH parsed AS (
  SELECT
    strptime(issue_d, '%b-%Y')::DATE                                  AS issue_date,
    CASE WHEN term LIKE '%36%' THEN 36 WHEN term LIKE '%60%' THEN 60 END AS term_months,
    loan_status LIKE 'Does not meet%'                                 AS off_policy,
    -- Strip the policy prefix so the underlying status is comparable.
    replace(loan_status, 'Does not meet the credit policy. Status:', '') AS status
  FROM read_csv(?, header = true, all_varchar = true)
  WHERE issue_d IS NOT NULL AND term IS NOT NULL AND loan_status IS NOT NULL
),

aged AS (
  SELECT
    *,
    date_diff('month', issue_date, DATE '2019-04-01') - term_months AS months_past_term
  FROM parsed
)

SELECT
  term_months,
  months_past_term,
  count(*)                                                            AS loans,
  round(100.0 * count(*) FILTER (WHERE status IN ('Fully Paid', 'Charged Off'))
        / count(*), 3)                                                AS pct_terminal,
  round(100.0 * count(*) FILTER (WHERE status = 'Fully Paid')  / count(*), 3) AS pct_fully_paid,
  round(100.0 * count(*) FILTER (WHERE status = 'Charged Off') / count(*), 3) AS pct_charged_off,
  round(100.0 * count(*) FILTER (WHERE status = 'Current')     / count(*), 3) AS pct_current,
  round(100.0 * count(*) FILTER (WHERE status = 'Late (31-120 days)') / count(*), 3) AS pct_late_31_120,
  round(100.0 * count(*) FILTER (WHERE status = 'In Grace Period')    / count(*), 3) AS pct_grace,
  round(100.0 * count(*) FILTER (WHERE status = 'Late (16-30 days)')  / count(*), 3) AS pct_late_16_30,
  count(*) FILTER (WHERE off_policy)                                  AS off_policy_loans
FROM aged
WHERE term_months IS NOT NULL AND months_past_term BETWEEN -6 AND 36
GROUP BY term_months, months_past_term
ORDER BY term_months, months_past_term
