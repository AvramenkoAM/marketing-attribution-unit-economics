-- ─────────────────────────────────────────────────────────────────────────────
-- 01_cac_by_channel.sql
-- CAC, spend efficiency and customer volume per channel.
-- Tables: marketing_spend(month, channel, spend, clicks, impressions)
--         customer_acquisitions(month, channel, new_customers, spend, cac)
-- ─────────────────────────────────────────────────────────────────────────────

-- Monthly CAC by channel
SELECT
    month,
    channel,
    spend,
    new_customers,
    ROUND(cac, 2) AS cac
FROM customer_acquisitions
ORDER BY month, channel;


-- 24-month average CAC and volume per channel
SELECT
    channel,
    ROUND(AVG(spend), 0)         AS avg_monthly_spend,
    ROUND(SUM(new_customers), 0) AS total_customers_acquired,
    ROUND(AVG(new_customers), 1) AS avg_monthly_customers,
    ROUND(AVG(cac), 2)           AS avg_cac,
    ROUND(MIN(cac), 2)           AS best_cac,
    ROUND(MAX(cac), 2)           AS worst_cac
FROM customer_acquisitions
GROUP BY channel
ORDER BY avg_cac ASC;


-- Blended CAC across all channels
SELECT
    month,
    SUM(spend)         AS total_spend,
    SUM(new_customers) AS total_new_customers,
    ROUND(SUM(spend) / SUM(new_customers), 2) AS blended_cac
FROM customer_acquisitions
GROUP BY month
ORDER BY month;


-- Budget share by channel per month
WITH monthly_totals AS (
    SELECT month, SUM(spend) AS total_spend
    FROM customer_acquisitions
    GROUP BY month
)
SELECT
    a.month,
    a.channel,
    a.spend,
    ROUND(100.0 * a.spend / mt.total_spend, 2) AS budget_share_pct
FROM customer_acquisitions a
JOIN monthly_totals mt ON a.month = mt.month
ORDER BY a.month, budget_share_pct DESC;
