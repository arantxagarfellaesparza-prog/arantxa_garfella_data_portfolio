-- Reconciles the conditioned funnel against overall conversion, at both grains.
--
-- Exists because the funnel above answers a narrower question than the business
-- case asks. The gap between "converts among viewers" and "converts among
-- everyone" IS the discovery leak that conditioning removes, so it is reported
-- rather than implied.
--
-- Two grains on purpose. The funnel runs at session grain (DECISIONS 001) while
-- the 1.64% baseline is per identifier: some identifiers need only one of
-- several visits to convert, so the identifier rate is structurally the higher
-- of the two. Mixing them silently would look like an arithmetic error.

SELECT
  'sessions'                                                          AS grain,
  count(*)                                                            AS total,
  count(*) FILTER (WHERE viewed_item)                                 AS reached_view_item,
  count(*) FILTER (WHERE purchased)                                   AS converted,
  round(100.0 * count(*) FILTER (WHERE viewed_item) / count(*), 2)    AS pct_reaching_view_item,
  round(100.0 * count(*) FILTER (WHERE purchased) / count(*), 2)      AS pct_converting_overall,
  round(100.0 * count(*) FILTER (WHERE purchased)
        / nullif(count(*) FILTER (WHERE viewed_item), 0), 2)          AS pct_converting_of_viewers
FROM sessions

UNION ALL

SELECT
  'identifiers',
  count(DISTINCT user_pseudo_id),
  count(DISTINCT user_pseudo_id) FILTER (WHERE viewed_item),
  count(DISTINCT user_pseudo_id) FILTER (WHERE purchased),
  round(100.0 * count(DISTINCT user_pseudo_id) FILTER (WHERE viewed_item)
        / count(DISTINCT user_pseudo_id), 2),
  round(100.0 * count(DISTINCT user_pseudo_id) FILTER (WHERE purchased)
        / count(DISTINCT user_pseudo_id), 2),
  round(100.0 * count(DISTINCT user_pseudo_id) FILTER (WHERE purchased)
        / nullif(count(DISTINCT user_pseudo_id) FILTER (WHERE viewed_item), 0), 2)
FROM sessions
