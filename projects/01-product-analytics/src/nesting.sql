-- How far the "funnel" is from an actual funnel.
--
-- A real funnel is nested: every session at step N passed through N-1. These are
-- the sessions that are not, and their volume is what tells the reader whether
-- step-to-step conversion means anything at all.

SELECT
  'purchased without begin_checkout'  AS violation,
  count(*)                            AS sessions
FROM sessions WHERE purchased AND NOT began_checkout
UNION ALL
SELECT 'purchased without add_to_cart',  count(*) FROM sessions WHERE purchased AND NOT added_to_cart
UNION ALL
SELECT 'purchased without view_item',    count(*) FROM sessions WHERE purchased AND NOT viewed_item
UNION ALL
SELECT 'checkout without add_to_cart',   count(*) FROM sessions WHERE began_checkout AND NOT added_to_cart
ORDER BY sessions DESC
