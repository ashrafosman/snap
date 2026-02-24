"""
Mock data for Executive Fiscal ROI Dashboard (local dev).
Synthetic time series with 2025-12-03 ingestion change and 2026-01-12 remediation.
"""
import pandas as pd

# Event dates for vertical markers
INGESTION_CHANGE_DATE = "2025-12-03"
REMEDIATION_DATE = "2026-01-12"

def _month_range(start: str, end: str) -> list[str]:
    months = pd.date_range(start=start, end=end, freq="MS")
    return [d.strftime("%Y-%m-%d") for d in months]


def get_regions() -> list[str]:
    return ["All", "Region A", "Region B", "Region C", "Region D"]


def get_per_timeseries(region: str | None = None) -> pd.DataFrame:
    """PER rate by month. Columns: month_start, region, per_rate, overpayment_usd, issued_benefits_usd."""
    months = _month_range("2024-01-01", "2026-02-01")
    # PER oscillates around 6%; latest month 6.4% to match dashboard
    base = [5.2, 5.5, 5.8, 6.1, 5.9, 6.2, 6.4, 5.7, 5.9, 6.0, 5.8, 6.1, 6.3, 5.9, 6.0, 6.2, 6.4, 6.1, 5.9, 5.8, 6.0, 5.9, 5.8, 6.0, 5.7, 5.8]
    n = len(months)
    per = (base * ((n // len(base)) + 1))[:n]
    per[-1] = 6.4  # current PER for KPI
    overpayment = [round(8e6 + i * 120000 + (per[i] - 5.5) * 1e6, 0) for i in range(n)]
    issued = [round(380e6 + i * 2.5e6, 0) for i in range(n)]
    issued[-1] = 440_100_000  # $440.1M latest month
    df = pd.DataFrame({
        "month_start": months,
        "region": "All",
        "per_rate": [round(p, 2) for p in per],
        "overpayment_usd": overpayment,
        "issued_benefits_usd": issued,
    })
    if region and region != "All":
        df["region"] = region
    return df


def get_income_latency_timeseries(region: str | None = None) -> pd.DataFrame:
    """Latency by month. Columns: month_start, region, median_latency_days, p90_latency_days."""
    months = _month_range("2024-03-01", "2026-02-01")
    n = len(months)
    # Baseline ~8d median, ~16d P90; spike after 2025-12-03, back down after 2026-01-12
    dec25_idx = next((i for i, m in enumerate(months) if m >= "2025-12-01"), n - 1)
    feb26_idx = next((i for i, m in enumerate(months) if m >= "2026-01-01"), n - 1)
    median = []
    p90 = []
    for i in range(n):
        if i <= dec25_idx - 1:
            med, p = 8, 16
        elif i <= feb26_idx - 1:
            med, p = 18, 32  # ingestion change spike
        else:
            med, p = 8, 16   # remediation
        median.append(med)
        p90.append(p)
    df = pd.DataFrame({
        "month_start": months,
        "region": "All",
        "median_latency_days": median,
        "p90_latency_days": p90,
    })
    if region and region != "All":
        df["region"] = region
    return df


def get_roi_scenario(target_per: float) -> dict:
    """Projected penalty exposure for a target PER. Returns projected_penalty_exposure_usd, penalty_reduction_usd, below_threshold."""
    # Mock: current penalty exposure ~10.9M; at 5.8% target we get 32K reduction
    current_penalty = 10_900_000
    reduction = round(32_000 + (6.4 - target_per) * 15_000, 0)
    projected = max(0, current_penalty - reduction)
    return {
        "target_per": target_per,
        "projected_penalty_exposure_usd": projected,
        "penalty_reduction_usd": reduction,
        "below_threshold": target_per < 6.0,
    }


def get_kpi_summary(region: str | None = None) -> dict:
    """Current KPIs: current_per, per_delta_pp, benefits_issued_usd, median_latency_days, p90_latency_days, total_overpayment_usd."""
    per_df = get_per_timeseries(region)
    lat_df = get_income_latency_timeseries(region)
    if per_df.empty or lat_df.empty:
        return {
            "current_per": 0.0,
            "per_delta_pp": 0.0,
            "benefits_issued_usd": 0.0,
            "median_latency_days": 0,
            "p90_latency_days": 0,
            "total_overpayment_usd": 0.0,
        }
    latest_per = per_df.iloc[-1]
    latest_lat = lat_df.iloc[-1]
    prev_per = per_df.iloc[-2]["per_rate"] if len(per_df) >= 2 else latest_per["per_rate"]
    return {
        "current_per": round(float(latest_per["per_rate"]), 1),
        "per_delta_pp": round(float(latest_per["per_rate"] - prev_per), 2),
        "benefits_issued_usd": float(latest_per["issued_benefits_usd"]),
        "median_latency_days": int(latest_lat["median_latency_days"]),
        "p90_latency_days": int(latest_lat["p90_latency_days"]),
        "total_overpayment_usd": 10_900_000.0,  # cumulative identified (mock)
    }
