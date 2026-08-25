-- The one surviving segmentation dimension: first visit versus return visit.
--
-- Browser, device and country were all burned in DECISIONS 002-003 -- two
-- contaminated, one degenerate. This one is derived from session ordering, which
-- the device contamination does not touch, and it is also the dimension the
-- business question turns on.
--
-- Session-level, so a single identifier contributes its first session to one row
-- and its later sessions to the other. That is deliberate: the question is
-- whether a *visit* behaves differently depending on whether the visitor has
-- been here before.

WITH ranked AS (
  SELECT
    *,
    row_number() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_us) AS session_rank
  FROM sessions
)

SELECT
  CASE WHEN session_rank = 1 THEN '1_first_visit' ELSE '2_return_visit' END AS segment,
  count(*)                                                                  AS sessions,
  round(100.0 * count(*) FILTER (WHERE viewed_item)  / count(*), 2)         AS pct_reaching_view,
  round(100.0 * count(*) FILTER (WHERE purchased)    / count(*), 2)         AS pct_purchasing,
  round(100.0 * count(*) FILTER (WHERE purchased)
        / nullif(count(*) FILTER (WHERE viewed_item), 0), 2)                AS pct_purchasing_of_viewers,
  round(100.0 * count(*) FILTER (WHERE began_checkout)
        / nullif(count(*) FILTER (WHERE viewed_item), 0), 2)                AS pct_checkout_of_viewers
FROM ranked
GROUP BY segment
ORDER BY segment
