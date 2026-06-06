"""
Synthetic marketing dataset generator.
Produces 3 CSV files that mirror real SaaS marketing data.
Run: python data/generate_marketing_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
OUT = Path(__file__).parent

# ── Channel configuration ─────────────────────────────────────────────────────
CHANNELS = {
    "google_ads": {
        "base_spend":        8_000,
        "cpc":               2.50,       # cost per click
        "conversion_rate":   0.032,      # clicks → customers
        "monthly_churn":     0.055,
        "arpu":              48.0,        # avg revenue per customer / month
        "gross_margin":      0.72,
        "spend_growth":      0.02,       # MoM spend growth
    },
    "facebook_ads": {
        "base_spend":        6_000,
        "cpc":               1.80,
        "conversion_rate":   0.020,
        "monthly_churn":     0.082,
        "arpu":              39.0,
        "gross_margin":      0.70,
        "spend_growth":      0.015,
    },
    "seo": {
        "base_spend":        2_000,
        "cpc":               0.0,        # no direct CPC
        "conversion_rate":   0.0,
        "monthly_churn":     0.038,
        "arpu":              55.0,       # organic = higher quality
        "gross_margin":      0.76,
        "spend_growth":      0.01,
    },
    "email": {
        "base_spend":        500,
        "cpc":               0.0,
        "conversion_rate":   0.0,
        "monthly_churn":     0.028,
        "arpu":              43.0,
        "gross_margin":      0.74,
        "spend_growth":      0.005,
    },
}

# Organic channel customer acquisition (driven by SEO traffic, not CPC)
ORGANIC_CUSTOMERS = {
    "seo":   {"base": 110, "growth": 0.035},
    "email": {"base": 42,  "growth": 0.020},
}

MONTHS = pd.date_range("2022-01-01", periods=24, freq="MS")

# ── 1. Marketing spend ────────────────────────────────────────────────────────
spend_rows = []
for ch, cfg in CHANNELS.items():
    for i, m in enumerate(MONTHS):
        spend = cfg["base_spend"] * (1 + cfg["spend_growth"]) ** i
        # Seasonal: Q4 +25% paid, Q1 -10%
        seasonal = 1.25 if m.month in (10, 11, 12) else 0.90 if m.month in (1, 2) else 1.0
        spend = round(spend * seasonal + np.random.normal(0, spend * 0.03), 2)

        if cfg["cpc"] > 0:
            clicks = int(spend / cfg["cpc"] * np.random.uniform(0.92, 1.08))
            impressions = clicks * int(np.random.uniform(18, 35))
        else:
            clicks = 0
            impressions = 0

        spend_rows.append({
            "month": m.strftime("%Y-%m"),
            "channel": ch,
            "spend": max(spend, 100),
            "clicks": clicks,
            "impressions": impressions,
        })

spend_df = pd.DataFrame(spend_rows)
spend_df.to_csv(OUT / "marketing_spend.csv", index=False)
print(f"marketing_spend.csv  {len(spend_df)} rows")

# ── 2. Customer acquisitions ──────────────────────────────────────────────────
acq_rows = []
for ch, cfg in CHANNELS.items():
    for i, m in enumerate(MONTHS):
        spend_row = spend_df[(spend_df["month"]==m.strftime("%Y-%m")) & (spend_df["channel"]==ch)].iloc[0]

        if cfg["cpc"] > 0:
            new_cust = int(spend_row["clicks"] * cfg["conversion_rate"]
                           * np.random.uniform(0.88, 1.12))
        else:
            base = ORGANIC_CUSTOMERS[ch]["base"]
            growth = ORGANIC_CUSTOMERS[ch]["growth"]
            new_cust = int(base * (1 + growth) ** i * np.random.uniform(0.85, 1.15))

        new_cust = max(new_cust, 1)
        cac = round(spend_row["spend"] / new_cust, 2)

        acq_rows.append({
            "month": m.strftime("%Y-%m"),
            "channel": ch,
            "new_customers": new_cust,
            "spend": spend_row["spend"],
            "cac": cac,
        })

acq_df = pd.DataFrame(acq_rows)
acq_df.to_csv(OUT / "customer_acquisitions.csv", index=False)
print(f"customer_acquisitions.csv  {len(acq_df)} rows")

# ── 3. Cohort LTV (survival model per channel) ────────────────────────────────
ltv_rows = []
for ch, cfg in CHANNELS.items():
    churn = cfg["monthly_churn"]
    arpu  = cfg["arpu"]
    margin = cfg["gross_margin"]

    for i, acq_month in enumerate(MONTHS):
        n0 = acq_df[(acq_df["month"]==acq_month.strftime("%Y-%m")) & (acq_df["channel"]==ch)]["new_customers"].values[0]
        remaining = n0

        for t in range(13):  # month 0–12
            revenue = round(remaining * arpu * np.random.uniform(0.95, 1.05), 2)
            ltv_rows.append({
                "acquisition_month": acq_month.strftime("%Y-%m"),
                "channel":           ch,
                "cohort_month":      t,
                "customers_active":  int(remaining),
                "monthly_revenue":   revenue,
                "gross_profit":      round(revenue * margin, 2),
            })
            # Apply churn with noise
            churn_rate = churn * np.random.uniform(0.85, 1.15)
            remaining = remaining * (1 - churn_rate)

ltv_df = pd.DataFrame(ltv_rows)
ltv_df.to_csv(OUT / "cohort_ltv.csv", index=False)
print(f"cohort_ltv.csv  {len(ltv_df)} rows")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n── Channel Summary (24-month average) ──")
summary = acq_df.groupby("channel").agg(
    avg_monthly_spend=("spend", "mean"),
    avg_new_customers=("new_customers", "mean"),
    avg_cac=("cac", "mean"),
).round(1)
for ch, cfg in CHANNELS.items():
    ltv = cfg["arpu"] * cfg["gross_margin"] / cfg["monthly_churn"]
    summary.loc[ch, "theoretical_ltv"] = round(ltv, 0)
    summary.loc[ch, "ltv_cac_ratio"] = round(ltv / summary.loc[ch, "avg_cac"], 1)
print(summary.to_string())
