"""
Executive Fiscal ROI Dashboard — SNAP Payment Error Rate & Income Latency Monitoring.
Streamlit app for Databricks; uses gold_snap_* and gold_income_latency_timeseries.
"""
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Must be first Streamlit command
st.set_page_config(
    page_title="Executive Fiscal ROI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Data layer (mock vs real from env)
import dashboard_data as data

# Event dates for chart markers
INGESTION_CHANGE_DATE = "2025-12-03"
REMEDIATION_DATE = "2026-01-12"
PER_THRESHOLD = 6.0
TARGET_PER_DEFAULT = 5.8

# Dark theme: plotly layout
CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e0e0e0", size=12),
    margin=dict(l=50, r=30, t=40, b=50),
    xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.3)"),
    yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.3)"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
)


def apply_dark_css():
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    [data-testid="stMetricValue"] { color: #fafafa; }
    [data-testid="stMetricLabel"] { color: #9ca3af; }
    h1, h2, h3 { color: #f3f4f6 !important; }
    .stMarkdown { color: #d1d5db; }
    div[data-testid="stVerticalBlock"] > div { background: rgba(17,24,39,0.8); border-radius: 8px; padding: 1rem; }
    </style>
    """, unsafe_allow_html=True)


def main():
    apply_dark_css()

    # Region selector (top right area)
    regions = data.get_regions()
    col_title, col_live, col_region = st.columns([2, 1, 1])
    with col_title:
        st.title("Executive Fiscal ROI")
        st.caption("SNAP Payment Error Rate & Income Latency Monitoring.")
    with col_live:
        st.markdown("**Live Data** · **Databricks Connected**")
    with col_region:
        region = st.selectbox("Region", regions, key="region", label_visibility="collapsed")
        st.caption("Region breakdown")

    # KPIs
    kpi = data.get_kpi_summary(region if region != "All" else None)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta = kpi["per_delta_pp"]
        st.metric(
            "CURRENT PER RATE",
            f"{kpi['current_per']}%",
            f"{delta:+.2f}pp",
            delta_color="inverse",
        )
        st.caption("Target: 5.8%")
    with c2:
        st.metric(
            "BENEFITS ISSUED",
            f"${kpi['benefits_issued_usd']/1e6:.1f}M",
            "Total issued benefits.",
        )
        st.caption("Period total.")
    with c3:
        st.metric(
            "MEDIAN LATENCY",
            f"{kpi['median_latency_days']}d",
            "Improved",
            delta_color="off",
        )
        st.caption(f"P90: {kpi['p90_latency_days']}d")
    with c4:
        st.metric(
            "TOTAL OVERPAYMENT",
            f"${kpi['total_overpayment_usd']/1e6:.1f}M",
            "Cumulative identified.",
        )

    st.divider()

    # Charts row
    per_df = data.get_per_timeseries(region if region != "All" else None)
    lat_df = data.get_income_latency_timeseries(region if region != "All" else None)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("PER Rate Trend")
        st.caption("Federal threshold at 6%.")
        if not per_df.empty:
            per_df = per_df.copy()
            per_df["month_start"] = pd.to_datetime(per_df["month_start"])
            # Use list of dates to avoid pandas Timestamp + int in Plotly
            x_vals = per_df["month_start"].dt.to_pydatetime()
            fig_per = go.Figure()
            fig_per.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=per_df["per_rate"].tolist(),
                    mode="lines",
                    name="PER %",
                    line=dict(color="#3b82f6", width=2),
                )
            )
            fig_per.add_hline(
                y=PER_THRESHOLD,
                line_dash="dash",
                line_color="red",
                annotation_text="Above Threshold",
                annotation_position="top right",
            )
            fig_per.update_layout(**CHART_LAYOUT)
            fig_per.update_yaxes(title="%", range=[0, None])
            fig_per.update_xaxes(title="")
            st.plotly_chart(fig_per, use_container_width=True)
        else:
            st.info("No PER time series data.")

    with chart_col2:
        st.subheader("Wage Ingestion Latency")
        st.caption("Median & P90 processing days.")
        if not lat_df.empty:
            lat_df = lat_df.copy()
            lat_df["month_start"] = pd.to_datetime(lat_df["month_start"])
            # Use list of dates to avoid pandas Timestamp + int in Plotly
            x_vals = lat_df["month_start"].dt.to_pydatetime()
            x_min = lat_df["month_start"].min().to_pydatetime()
            x_max = lat_df["month_start"].max().to_pydatetime()
            fig_lat = go.Figure()
            fig_lat.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=lat_df["median_latency_days"].tolist(),
                    mode="lines",
                    name="Median",
                    line=dict(color="#3b82f6", width=2),
                )
            )
            fig_lat.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=lat_df["p90_latency_days"].tolist(),
                    mode="lines",
                    name="P90",
                    line=dict(color="#a855f7", width=2, dash="dash"),
                )
            )
            # Vertical lines: ingestion change & remediation (add_shape to avoid add_vline mean/sum on mixed types)
            y_max_lat = max(lat_df["median_latency_days"].max(), lat_df["p90_latency_days"].max())
            for label, date_str in [
                ("Ingestion change", INGESTION_CHANGE_DATE),
                ("Remediation", REMEDIATION_DATE),
            ]:
                d = pd.Timestamp(date_str).to_pydatetime()
                if x_min <= d <= x_max:
                    fig_lat.add_shape(
                        type="line",
                        x0=d, x1=d,
                        y0=0, y1=y_max_lat,
                        xref="x", yref="y",
                        line=dict(color="orange", dash="dot", width=1.5),
                    )
                    fig_lat.add_annotation(
                        x=d, y=y_max_lat, yref="y", xref="x",
                        text=label, showarrow=False,
                        yanchor="bottom", font=dict(size=10, color="orange"),
                    )
            fig_lat.update_layout(**CHART_LAYOUT)
            fig_lat.update_yaxes(title="Days", range=[0, None])
            fig_lat.update_xaxes(title="")
            st.plotly_chart(fig_lat, use_container_width=True)
        else:
            st.info("No latency time series data.")

    st.divider()

    # Scenario Simulator
    st.subheader("Scenario Simulator")
    st.caption("Adjust target PER rate to see projected penalty exposure.")
    target_per = st.slider(
        "Target PER %",
        min_value=4.0,
        max_value=8.0,
        value=float(TARGET_PER_DEFAULT),
        step=0.1,
        format="%.1f%%",
        key="target_per",
    )
    scenario = data.get_roi_scenario(target_per)
    sim_c1, sim_c2, sim_c3 = st.columns(3)
    with sim_c1:
        st.metric("Target Rate", f"{target_per:.1f}%", "")
    with sim_c2:
        st.metric(
            "Est. Penalty Reduction",
            f"${scenario['penalty_reduction_usd']/1e3:.0f}K",
            "",
        )
    with sim_c3:
        st.metric(
            "Below Threshold",
            "Yes" if scenario["below_threshold"] else "No",
            "",
        )
    st.caption("Target PER 5.8% by 2026-03.")
    if not scenario["below_threshold"]:
        st.warning("Target is at or above federal 6% threshold.")

    # Sidebar: data source indicator
    with st.sidebar:
        st.header("Data sources")
        st.markdown("""
        - **gold_snap_per_timeseries**
        - **gold_snap_roi_scenarios**
        - **gold_income_latency_timeseries**
        """)
        if os.getenv("USE_MOCK_BACKEND", "true").lower() == "true":
            st.info("Using **mock** data (local).")
        else:
            st.success("**Live** Databricks data.")


if __name__ == "__main__":
    main()
