"""
Real data layer: queries gold_snap_per_timeseries, gold_snap_roi_scenarios, gold_income_latency_timeseries.
Set DATABRICKS_WAREHOUSE_ID and optionally SNAP_CATALOG, SNAP_SCHEMA in app resources.
"""
import os
import pandas as pd
from databricks.sdk.core import Config
from databricks import sql

_CATALOG = os.getenv("SNAP_CATALOG", "main")
_SCHEMA = os.getenv("SNAP_SCHEMA", "default")


def _get_conn():
    cfg = Config()
    wh_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not wh_id:
        raise RuntimeError("DATABRICKS_WAREHOUSE_ID not set. Add SQL warehouse in app resources.")
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{wh_id}",
        credentials_provider=lambda: cfg.authenticate,
    )


def _run_query(query: str) -> pd.DataFrame:
    conn = _get_conn()
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def get_regions() -> list[str]:
    q = f"""
    SELECT DISTINCT COALESCE(region, 'All') AS region
    FROM {_CATALOG}.{_SCHEMA}.gold_snap_per_timeseries
    ORDER BY region
    """
    df = _run_query(q)
    return ["All"] + df["region"].astype(str).tolist()


def get_per_timeseries(region: str | None = None) -> pd.DataFrame:
    where = f" AND region = '{region}'" if region and region != "All" else ""
    q = f"""
    SELECT month_start, region, per_rate, overpayment_usd, issued_benefits_usd
    FROM {_CATALOG}.{_SCHEMA}.gold_snap_per_timeseries
    WHERE 1=1 {where}
    ORDER BY month_start
    """
    return _run_query(q)


def get_income_latency_timeseries(region: str | None = None) -> pd.DataFrame:
    where = f" AND region = '{region}'" if region and region != "All" else ""
    q = f"""
    SELECT month_start, region, median_latency_days, p90_latency_days
    FROM {_CATALOG}.{_SCHEMA}.gold_income_latency_timeseries
    WHERE 1=1 {where}
    ORDER BY month_start
    """
    return _run_query(q)


def get_roi_scenario(target_per: float) -> dict:
    q = f"""
    SELECT per_rate_projected, projected_penalty_exposure_usd
    FROM {_CATALOG}.{_SCHEMA}.gold_snap_roi_scenarios
    WHERE target_per = {target_per}
    ORDER BY scenario_date DESC
    LIMIT 1
    """
    df = _run_query(q)
    if df.empty:
        return {
            "target_per": target_per,
            "projected_penalty_exposure_usd": 0,
            "penalty_reduction_usd": 0,
            "below_threshold": target_per < 6.0,
        }
    row = df.iloc[0]
    # Assume current from KPI; reduction = current - projected
    current = float(os.getenv("CURRENT_PENALTY_EXPOSURE", "10900000"))
    projected = float(row["projected_penalty_exposure_usd"])
    return {
        "target_per": target_per,
        "projected_penalty_exposure_usd": projected,
        "penalty_reduction_usd": max(0, current - projected),
        "below_threshold": target_per < 6.0,
    }


def get_kpi_summary(region: str | None = None) -> dict:
    per_df = get_per_timeseries(region)
    lat_df = get_income_latency_timeseries(region)
    if per_df.empty:
        return {
            "current_per": 0.0,
            "per_delta_pp": 0.0,
            "benefits_issued_usd": 0.0,
            "median_latency_days": 0,
            "p90_latency_days": 0,
            "total_overpayment_usd": 0.0,
        }
    latest_per = per_df.iloc[-1]
    prev_per = per_df.iloc[-2]["per_rate"] if len(per_df) >= 2 else latest_per["per_rate"]
    benefits = per_df["issued_benefits_usd"].sum()
    overpayment = per_df["overpayment_usd"].sum()
    median_lat = int(lat_df.iloc[-1]["median_latency_days"]) if not lat_df.empty else 0
    p90_lat = int(lat_df.iloc[-1]["p90_latency_days"]) if not lat_df.empty else 0
    return {
        "current_per": round(float(latest_per["per_rate"]), 1),
        "per_delta_pp": round(float(latest_per["per_rate"] - prev_per), 2),
        "benefits_issued_usd": float(benefits),
        "median_latency_days": median_lat,
        "p90_latency_days": p90_lat,
        "total_overpayment_usd": float(overpayment),
    }
