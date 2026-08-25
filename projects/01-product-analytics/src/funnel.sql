-- Purchase funnel, session grain, conditioned on sessions that viewed an item.
--
-- Denominator choice (DECISIONS 001, 004): sessions with view_item, because the
-- business question is about the purchase path. The cost is that the largest
-- drop in the dataset -- 77.3% of identifiers never view a product at all -- sits
-- outside this funnel by construction. It is recovered in the reconciliation
-- query below rather than left unsaid.
--
-- Steps are NOT nested subsets. add_to_cart does not fire on a large share of
-- purchase paths (DECISIONS 004), so requiring it would discard ~40% of real
-- conversions. Each step counts sessions carrying that flag, independently, and
-- the nesting violations are reported separately so the reader can see how far
-- from a true funnel this is.

WITH viewers AS (
  SELECT * FROM sessions WHERE viewed_item
),

steps AS (
            SELECT 1 AS step_order, 'view_item'        AS step, count(*)                                  AS sessions FROM viewers
  UNION ALL SELECT 2,               'add_to_cart',              count(*) FILTER (WHERE added_to_cart)                  FROM viewers
  UNION ALL SELECT 3,               'begin_checkout',           count(*) FILTER (WHERE began_checkout)                 FROM viewers
  UNION ALL SELECT 4,               'add_payment_info',         count(*) FILTER (WHERE added_payment_info)             FROM viewers
  UNION ALL SELECT 5,               'purchase',                 count(*) FILTER (WHERE purchased)                      FROM viewers
)

SELECT
  step_order,
  step,
  sessions,
  -- Share of the funnel's own denominator: what survives from the top.
  round(100.0 * sessions / first_value(sessions) OVER (ORDER BY step_order), 2) AS pct_of_viewers,
  -- Step-to-step. Meaningless where a step is non-exhaustive; read with the note above.
  round(100.0 * sessions / lag(sessions) OVER (ORDER BY step_order), 2)         AS pct_of_previous
FROM steps
ORDER BY step_order
