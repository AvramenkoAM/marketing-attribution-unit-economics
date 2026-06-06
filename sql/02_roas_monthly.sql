-- ─────────────────────────────────────────────────────────────────────────────
-- 02_roas_monthly.sql
-- ROAS = Revenue / Spend. Revenue approximated as new_customers × ARPU.
-- For cohort-based ROAS use cohort_ltv table.
-- ─────────────────────────────────────────────────────────────────────────────

-- Monthly ROAS per channel (Month-0 revenue approximation)
WITH arpu AS (
    SELECT 'google_ads'   AS channel, 48.0 AS monthly_arpu UNION ALL
    SELECT 'facebook_ads',            39.0               UNION ALL
    SELECT 'seo',                     55.0               UNION ALL
    SELECT 'email',                   43.0
)
SELECT
    a.month,
    a.channel,
    a.spend,
    a.new_customers,
    ROUND(a.new_customers * ar.monthly_arpu, 2)                AS month0_revenue,
    ROUND(a.new_customers * ar.monthly_arpu / a.spend, 2)      AS roas_month0
FROM customer_acquisitions a
JOIN arpu ar ON a.channel = ar.channel
ORDER BY a.month, roas_month0 DESC;


-- Average ROAS by channel (24-month)
WITH arpu AS (
    SELECT 'google_ads' AS channel, 48.0 AS monthly_arpu UNION ALL
    SELECT 'facebook_ads', 39.0 UNION ALL
    SELECT 'seo', 55.0 UNION ALL
    SELECT 'email', 43.0
)
SELECT
    a.channel,
    ROUND(SUM(a.new_customers * ar.monthly_arpu), 0)               AS total_revenue_m0,
    ROUND(SUM(a.spend), 0)                                         AS total_spend,
    ROUND(SUM(a.new_customers * ar.monthly_arpu) / SUM(a.spend), 2) AS avg_roas
FROM customer_acquisitions a
JOIN arpu ar ON a.channel = ar.channel
GROUP BY a.channel
ORDER BY avg_roas DESC;


-- 12-month cohort ROAS — total gross profit vs CAC investment
SELECT
    l.channel,
    ROUND(AVG(l.gross_profit), 2)                     AS avg_monthly_gross_profit,
    ROUND(SUM(l.gross_profit) / COUNT(DISTINCT l.acquisition_month), 2) AS avg_12m_gp_per_cohort,
    ROUND(AVG(a.cac), 2)                              AS avg_cac,
    ROUND(
        SUM(l.gross_profit) / COUNT(DISTINCT l.acquisition_month)
        / AVG(a.cac),
        2
    )                                                  AS cohort_roas_12m
FROM cohort_ltv l
JOIN (SELECT channel, AVG(cac) AS cac FROM customer_acquisitions GROUP BY channel) a
  ON l.channel = a.channel
GROUP BY l.channel
ORDER BY cohort_roas_12m DESC;
