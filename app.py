import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Marketing Attribution & Unit Economics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
TEAL, ORANGE, NAVY, YELLOW, GRAY = "#2a9d8f","#e76f51","#264653","#e9c46a","#8d9db6"

COLORS = {"google_ads": TEAL, "facebook_ads": ORANGE, "seo": NAVY, "email": YELLOW}
LABELS = {"google_ads":"Google Ads","facebook_ads":"Facebook Ads","seo":"SEO","email":"Email"}

PARAMS = {
    "google_ads":   {"arpu":48.0,"margin":0.72,"churn":0.055,"max_scale":15000},
    "facebook_ads": {"arpu":39.0,"margin":0.70,"churn":0.082,"max_scale": 8000},
    "seo":          {"arpu":55.0,"margin":0.76,"churn":0.038,"max_scale": 8000},
    "email":        {"arpu":43.0,"margin":0.74,"churn":0.028,"max_scale": 2000},
}

@st.cache_data
def load():
    spend = pd.read_csv(ROOT/"data"/"marketing_spend.csv")
    acq   = pd.read_csv(ROOT/"data"/"customer_acquisitions.csv")
    cohort= pd.read_csv(ROOT/"data"/"cohort_ltv.csv")
    return spend, acq, cohort

spend_df, acq_df, cohort_df = load()

def ltv(ch): p=PARAMS[ch]; return p["arpu"]*p["margin"]/p["churn"]
def payback(ch, cac): p=PARAMS[ch]; return cac/(p["arpu"]*p["margin"])

avg_cac = acq_df.groupby("channel")["cac"].mean()

with st.sidebar:
    st.markdown("## 📊 Marketing Analytics")
    st.caption("SaaS · 4 channels · 24 months")
    st.divider()
    page = st.radio("Go to",
        ["Overview","Channel Analysis","LTV & Payback","Budget Optimizer"],
        label_visibility="collapsed")
    st.divider()
    st.caption("Stack: Python · SQL · openpyxl · Streamlit · Plotly")

# ── OVERVIEW ─────────────────────────────────────────────────────────────────
if page == "Overview":
    st.header("Marketing Overview")

    total_spend = acq_df["spend"].sum()
    total_cust  = acq_df["new_customers"].sum()
    blended_cac = total_spend / total_cust
    best_ch     = avg_cac.idxmin()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Spend (24 mo)", f"${total_spend:,.0f}")
    c2.metric("Total Customers",     f"{total_cust:,}")
    c3.metric("Blended CAC",         f"${blended_cac:.2f}")
    c4.metric("Best Channel",        LABELS[best_ch], f"CAC ${avg_cac[best_ch]:.2f}")

    st.divider()
    l, r = st.columns(2)

    with l:
        st.subheader("Budget Share by Channel")
        ch_spend = acq_df.groupby("channel")["spend"].sum().reset_index()
        ch_spend["label"] = ch_spend["channel"].map(LABELS)
        fig = px.pie(ch_spend, names="label", values="spend", hole=0.5,
                     color="channel", color_discrete_map={c: COLORS[c] for c in COLORS})
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with r:
        st.subheader("Average CAC by Channel")
        cac_data = avg_cac.reset_index()
        cac_data["label"] = cac_data["channel"].map(LABELS)
        cac_data = cac_data.sort_values("cac")
        fig = px.bar(cac_data, x="cac", y="label", orientation="h",
                     color="channel", color_discrete_map={c: COLORS[c] for c in COLORS},
                     labels={"cac":"Avg CAC ($)","label":""})
        fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=20,b=0))
        fig.add_vline(x=50, line_dash="dot", line_color=GRAY, annotation_text="$50 threshold")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Monthly New Customers by Channel")
    monthly_cust = acq_df.copy()
    monthly_cust["label"] = monthly_cust["channel"].map(LABELS)
    fig = px.bar(monthly_cust, x="month", y="new_customers", color="channel",
                 color_discrete_map={c: COLORS[c] for c in COLORS},
                 labels={"month":"","new_customers":"New Customers","channel":""},
                 barmode="stack")
    fig.update_layout(margin=dict(l=0,r=0,t=20,b=0))
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

# ── CHANNEL ANALYSIS ─────────────────────────────────────────────────────────
elif page == "Channel Analysis":
    st.header("Channel Deep Dive")

    selected = st.selectbox("Select channel", list(LABELS.values()),
                            index=0)
    ch_key = {v:k for k,v in LABELS.items()}[selected]
    color  = COLORS[ch_key]
    p      = PARAMS[ch_key]
    cac_v  = avg_cac[ch_key]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Avg Monthly Spend",  f"${acq_df[acq_df['channel']==ch_key]['spend'].mean():,.0f}")
    c2.metric("Avg New Customers",  f"{acq_df[acq_df['channel']==ch_key]['new_customers'].mean():.0f}")
    c3.metric("Avg CAC",            f"${cac_v:.2f}")
    c4.metric("LTV",                f"${ltv(ch_key):,.0f}")
    c5.metric("LTV/CAC",            f"{ltv(ch_key)/cac_v:.1f}x")

    st.divider()
    l, r = st.columns(2)

    ch_data = acq_df[acq_df["channel"]==ch_key]
    with l:
        st.subheader(f"Monthly CAC — {selected}")
        fig = px.line(ch_data, x="month", y="cac",
                      labels={"month":"","cac":"CAC ($)"},
                      color_discrete_sequence=[color], markers=True)
        fig.update_traces(line_width=2)
        fig.add_hline(y=cac_v, line_dash="dash", line_color=GRAY,
                      annotation_text=f"Avg ${cac_v:.2f}")
        fig.update_layout(margin=dict(l=0,r=0,t=20,b=0))
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    with r:
        st.subheader(f"Monthly New Customers — {selected}")
        fig = px.bar(ch_data, x="month", y="new_customers",
                     labels={"month":"","new_customers":"New Customers"},
                     color_discrete_sequence=[color])
        fig.update_layout(margin=dict(l=0,r=0,t=20,b=0))
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Payback Curve — {selected}")
    months_arr = np.arange(0, 25)
    cum_gp = np.array([p["arpu"]*p["margin"]*(1-(1-p["churn"])**t)/p["churn"]
                       for t in months_arr])
    pb_month = payback(ch_key, cac_v)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months_arr, y=cum_gp, name="Cumulative GP",
                             line=dict(color=color, width=2)))
    fig.add_hline(y=cac_v, line_dash="dash", line_color=ORANGE,
                  annotation_text=f"CAC = ${cac_v:.2f}")
    fig.add_vline(x=pb_month, line_dash="dot", line_color=GRAY,
                  annotation_text=f"Payback: {pb_month:.1f} mo")
    fig.update_layout(xaxis_title="Months Since Acquisition",
                      yaxis_title="Cumulative Gross Profit / Customer ($)",
                      margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig, use_container_width=True)

# ── LTV & PAYBACK ────────────────────────────────────────────────────────────
elif page == "LTV & Payback":
    st.header("LTV & Payback Analysis")

    metrics = []
    for ch, p in PARAMS.items():
        cac_v = avg_cac[ch]
        metrics.append({
            "Channel": LABELS[ch],
            "LTV ($)": int(ltv(ch)),
            "CAC ($)": round(cac_v, 2),
            "LTV/CAC": round(ltv(ch)/cac_v, 1),
            "Payback (mo)": round(payback(ch, cac_v), 1),
            "Monthly Churn": f"{p['churn']:.1%}",
        })
    st.dataframe(pd.DataFrame(metrics), use_container_width=True, hide_index=True)

    st.divider()
    l, r = st.columns(2)

    with l:
        st.subheader("LTV / CAC Ratio")
        ltv_cac_data = [(LABELS[ch], ltv(ch)/avg_cac[ch]) for ch in PARAMS]
        ltv_cac_data.sort(key=lambda x: x[1])
        fig = go.Figure(go.Bar(
            x=[v for _, v in ltv_cac_data],
            y=[n for n, _ in ltv_cac_data],
            orientation="h",
            marker_color=[COLORS[k] for k in ["email","seo","google_ads","facebook_ads"]],
            text=[f"{v:.1f}x" for _, v in ltv_cac_data],
            textposition="outside",
        ))
        fig.add_vline(x=3,  line_dash="dot", line_color=ORANGE, annotation_text="Min 3x")
        fig.add_vline(x=10, line_dash="dot", line_color=TEAL,   annotation_text="Good 10x")
        fig.update_layout(xaxis_title="LTV/CAC Ratio", margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with r:
        st.subheader("Survival Curves")
        surv = cohort_df.groupby(["channel","cohort_month"])["customers_active"].mean().reset_index()
        m0   = surv[surv["cohort_month"]==0].set_index("channel")["customers_active"]
        surv["retention"] = surv.apply(lambda r: r["customers_active"]/m0[r["channel"]], axis=1)
        fig = px.line(surv, x="cohort_month", y="retention",
                      color="channel", color_discrete_map={c: COLORS[c] for c in COLORS},
                      labels={"cohort_month":"Months Since Acquisition",
                              "retention":"Retention Rate","channel":""},
                      markers=False)
        fig.update_layout(yaxis_tickformat=".0%", margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

# ── BUDGET OPTIMIZER ─────────────────────────────────────────────────────────
elif page == "Budget Optimizer":
    st.header("Budget Optimizer")
    st.caption("Adjust channel budgets below. Total is fixed at $16 500/month.")

    TOTAL = 16_500
    current = {"google_ads":8000,"facebook_ads":6000,"seo":2000,"email":500}

    st.subheader("Set Monthly Budget per Channel")
    cols = st.columns(4)
    new_budget = {}
    for i, (ch, label) in enumerate(LABELS.items()):
        new_budget[ch] = cols[i].slider(
            label, min_value=0, max_value=12000,
            value=current[ch], step=250, key=ch
        )

    total_set = sum(new_budget.values())
    delta = total_set - TOTAL
    if abs(delta) > 50:
        st.warning(f"Total: **${total_set:,}** — ${abs(delta):,} "
                   f"{'over' if delta>0 else 'under'} budget. Adjust sliders to reach $16 500.")
    else:
        st.success(f"Total: **${total_set:,}** ✓")

    st.divider()

    def projected(budget):
        results = {}
        for ch, p in PARAMS.items():
            s = budget[ch]
            c = avg_cac[ch]
            if c > 20:
                base = current[ch] / c
                scale = (s / current[ch]) ** 0.85 if s > 0 else 0
                results[ch] = max(int(base * scale), 0)
            else:
                base = current[ch] / c
                scale = min(s / current[ch], p["max_scale"]/current[ch])
                results[ch] = max(int(base * scale), 0) if s > 0 else 0
        return results

    cur_proj = projected(current)
    new_proj = projected(new_budget)

    c1,c2,c3,c4 = st.columns(4)
    metrics_cols = [c1,c2,c3,c4]
    for i, ch in enumerate(LABELS):
        delta_c = new_proj[ch] - cur_proj[ch]
        metrics_cols[i].metric(LABELS[ch],
                                f"{new_proj[ch]:,} customers",
                                f"{delta_c:+,}")

    st.divider()
    l, r = st.columns(2)

    with l:
        st.subheader("Budget: Current vs New")
        comp = pd.DataFrame({
            "Channel":  [LABELS[ch] for ch in LABELS],
            "Current":  [current[ch] for ch in LABELS],
            "New":      [new_budget[ch] for ch in LABELS],
        })
        fig = px.bar(comp.melt("Channel"), x="Channel", y="value", color="variable",
                     barmode="group",
                     color_discrete_map={"Current":GRAY, "New":TEAL},
                     labels={"value":"Budget ($)","variable":"","Channel":""})
        fig.update_layout(margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with r:
        st.subheader("Projected Monthly Customers")
        comp_c = pd.DataFrame({
            "Channel":  [LABELS[ch] for ch in LABELS],
            "Current":  [cur_proj[ch] for ch in LABELS],
            "Projected":[new_proj[ch] for ch in LABELS],
        })
        fig = px.bar(comp_c.melt("Channel"), x="Channel", y="value", color="variable",
                     barmode="group",
                     color_discrete_map={"Current":GRAY, "Projected":TEAL},
                     labels={"value":"New Customers","variable":"","Channel":""})
        fig.update_layout(margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    total_cur = sum(cur_proj.values())
    total_new = sum(new_proj.values())
    blended_cur = TOTAL / total_cur if total_cur else 0
    blended_new = total_set / total_new if total_new else 0
    delta_cust  = total_new - total_cur

    st.info(
        f"**Summary:** {total_cur:,} → {total_new:,} customers/month  "
        f"(**{delta_cust:+,}**, {delta_cust/total_cur*100:+.1f}%)  |  "
        f"Blended CAC: ${blended_cur:.2f} → ${blended_new:.2f}"
    )
