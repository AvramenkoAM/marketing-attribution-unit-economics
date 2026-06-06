-- ─────────────────────────────────────────────────────────────────────────────
-- 03_ltv_cohorts.sql
-- Cohort-based LTV analysis using the cohort_ltv table.
-- Table: cohort_ltv(acquisition_month, channel, cohort_month,
--                   customers_active, monthly_revenue, gross_profit)
-- ─────────────────────────────────────────────────────────────────────────────

-- Average retention rate at each cohort month by channel
SELECT
    channel,
    cohort_month,
    ROUND(AVG(customers_active), 1) AS avg_customers_active,
    ROUND(
        AVG(customers_active) * 100.0
        / AVG(CASE WHEN cohort_month = 0 THEN customers_active END)
            OVER (PARTITION BY channel),
        2
    ) AS retention_pct
FROM cohort_ltv
GROUP BY channel, cohort_month
ORDER BY channel, cohort_month;


-- Cumulative gross profit per acquired customer by channel (12-month LTV proxy)
WITH cohort_totals AS (
    SELECT
        channel,
        acquisition_month,
        SUM(gross_profit)                                    AS total_gp_12m,
        MAX(CASE WHEN cohort_month = 0 THEN customers_active END) AS cohort_size
    FROM cohort_ltv
    GROUP BY channel, acquisition_month
)
SELECT
    channel,
    ROUND(AVG(total_gp_12m), 2)                AS avg_12m_gross_profit_per_cohort,
    ROUND(AVG(total_gp_12m / cohort_size), 2)  AS avg_12m_ltv_per_customer,
    COUNT(*)                                   AS cohorts_measured
FROM cohort_totals
GROUP BY channel
ORDER BY avg_12m_ltv_per_customer DESC;


-- Monthly revenue trend from all active cohorts (total MRR proxy)
SELECT
    acquisition_month,
    channel,
    SUM(monthly_revenue) AS monthly_revenue,
    SUM(gross_profit)    AS gross_profit,
    SUM(customers_active) AS customers_active
FROM cohort_ltv
WHERE cohort_month BETWEEN 1 AND 12
GROUP BY acquisition_month, channel
ORDER BY acquisition_month, channel;


-- Payback period: first cohort_month where cumulative GP ≥ CAC × cohort_size
WITH cum_gp AS (
    SELECT
        l.channel,
        l.acquisition_month,
        l.cohort_month,
        SUM(l.gross_profit) OVER (
            PARTITION BY l.channel, l.acquisition_month
            ORDER BY l.cohort_month
        ) AS cum_gross_profit,
        MAX(CASE WHEN l.cohort_month = 0 THEN l.customers_active END)
            OVER (PARTITION BY l.channel, l.acquisition_month) AS cohort_size,
        a.cac
    FROM cohort_ltv l
    JOIN customer_acquisitions a
        ON l.channel = a.channel AND l.acquisition_month = a.month
)
SELECT
    channel,
    ROUND(AVG(cohort_month), 1) AS avg_payback_months,
    MIN(cohort_month)           AS fastest_payback,
    MAX(cohort_month)           AS slowest_payback
FROM cum_gp
WHERE cum_gross_profit >= cac * cohort_size
  AND cohort_month = (
      SELECT MIN(c2.cohort_month)
      FROM cum_gp c2
      WHERE c2.channel = cum_gp.channel
        AND c2.acquisition_month = cum_gp.acquisition_month
        AND c2.cum_gross_profit >= c2.cac * c2.cohort_size
  )
GROUP BY channel
ORDER BY avg_payback_months;
