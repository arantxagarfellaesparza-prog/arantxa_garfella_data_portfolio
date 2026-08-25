-- Session-level extract from the public GA4 e-commerce sample.
--
-- This file is the reproducible artefact, not the CSV it produces. The snapshot
-- is pinned with a checksum because a public dataset can be revised or withdrawn,
-- and "re-run the script" is only as stable as the source it reads.
--
-- Grain: one row per (user_pseudo_id, ga_session_id). This is the finest grain
-- the analysis needs, so identifier-level views (retention, experiment
-- assignment) are derived from it locally rather than exported separately.
--
-- Source:  bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
-- Period:  2020-11-01 to 2021-01-31 (92 daily tables, ~4.3M events)
-- Expected output: ~355k rows
--
-- Known defects carried by this extract, established in DECISIONS 002-004:
--   * browser / device_category are contaminated at ~3.1% of identifiers
--     (reassigned per event) -- unusable as segmentation dimensions
--   * geo.country is degenerate (forced constant per identifier) and is
--     deliberately NOT exported, so it cannot be used by accident
--   * add_to_cart does not fire on a large share of purchase paths
--   * begin_checkout and add_shipping_info fire together, so they are one step

WITH ev AS (
  SELECT
    user_pseudo_id,
    (SELECT value.int_value
     FROM UNNEST(event_params)
     WHERE key = 'ga_session_id')       AS ga_session_id,
    PARSE_DATE('%Y%m%d', event_date)    AS event_date,
    event_timestamp,
    event_name,
    device.category                     AS device_category,
    device.web_info.browser             AS browser,
    traffic_source.medium               AS traffic_medium,
    traffic_source.source               AS traffic_source
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
)

SELECT
  -- Emitted untransformed. It is fragile in a spreadsheet -- the value looks
  -- numeric and a European locale reads the dot as a thousands separator, which
  -- destroys it -- so the defence is the export route in data/README.md, not a
  -- transformation here. Keeping the raw column means the committed query and
  -- the pinned snapshot are the same artefact.
  user_pseudo_id,
  ga_session_id,
  MIN(event_date)                              AS session_date,
  MIN(event_timestamp)                         AS session_start_us,
  COUNT(*)                                     AS n_events,

  -- Funnel flags. add_shipping_info is folded into began_checkout on purpose:
  -- the two fire under 5ms apart, so they are one step (DECISIONS 004).
  COUNTIF(event_name = 'view_item')       > 0  AS viewed_item,
  COUNTIF(event_name = 'add_to_cart')     > 0  AS added_to_cart,
  COUNTIF(event_name IN ('begin_checkout',
                         'add_shipping_info')) > 0 AS began_checkout,
  COUNTIF(event_name = 'add_payment_info') > 0 AS added_payment_info,
  COUNTIF(event_name = 'purchase')        > 0  AS purchased,
  COUNTIF(event_name = 'purchase')             AS n_purchases,

  -- session_start is exported to audit defect 4: 3,038 identifiers appear to
  -- have a session without one.
  COUNTIF(event_name = 'session_start')   > 0  AS has_session_start,
  COUNTIF(event_name = 'first_visit')     > 0  AS has_first_visit,

  -- Dimensions. Kept so their quality can be audited locally, NOT because they
  -- are trusted: browser and device_category are known-contaminated, and
  -- traffic_* still needs its `<Other>` rate measured before use.
  ANY_VALUE(device_category)                   AS device_category,
  ANY_VALUE(browser)                           AS browser,
  ANY_VALUE(traffic_medium)                    AS traffic_medium,
  ANY_VALUE(traffic_source)                    AS traffic_source

FROM ev
WHERE ga_session_id IS NOT NULL
GROUP BY user_pseudo_id, ga_session_id
