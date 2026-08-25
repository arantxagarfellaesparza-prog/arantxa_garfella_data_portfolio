-- The six quantities the lever comparison rests on, in one place so the
-- sensitivity analysis cannot silently drift from the data.
--
-- Purchases decompose multiplicatively:
--     purchases = sessions x P(view) x P(buy | view)
-- which is what makes discovery and conversion comparable at all. Retention sits
-- outside that identity: it changes the number of sessions rather than a
-- conditional rate, so it is modelled separately.

WITH ranked AS (
  SELECT
    user_pseudo_id,
    viewed_item,
    purchased,
    row_number() OVER (PARTITION BY user_pseudo_id ORDER BY session_start_us) AS rk,
    count(*)     OVER (PARTITION BY user_pseudo_id)                           AS n_sessions
  FROM sessions
),

per_user AS (
  SELECT
    user_pseudo_id,
    max(n_sessions)                                        AS n_sessions,
    max(CASE WHEN rk >= 2 AND purchased THEN 1 ELSE 0 END) AS bought_later
  FROM ranked
  GROUP BY user_pseudo_id
)

SELECT
  (SELECT count(*) FROM sessions)                                    AS sessions,
  (SELECT count(DISTINCT user_pseudo_id) FROM sessions)              AS identifiers,
  (SELECT count(*) FILTER (WHERE viewed_item) / count(*)::DOUBLE
   FROM sessions)                                                    AS p_view,
  (SELECT count(*) FILTER (WHERE purchased)
        / nullif(count(*) FILTER (WHERE viewed_item), 0)::DOUBLE
   FROM sessions)                                                    AS p_buy_given_view,
  count(*) FILTER (WHERE n_sessions >= 2) / count(*)::DOUBLE         AS p_return,
  count(*) FILTER (WHERE n_sessions >= 2 AND bought_later = 1)
        / nullif(count(*) FILTER (WHERE n_sessions >= 2), 0)::DOUBLE AS p_buy_after_return
FROM per_user
