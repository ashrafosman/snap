"""
Data layer for Executive Fiscal ROI Dashboard.
Uses gold_snap_per_timeseries, gold_snap_roi_scenarios, gold_income_latency_timeseries.
"""
import os
from datetime import datetime

USE_MOCK = os.getenv("USE_MOCK_BACKEND", "true").lower() == "true"

if USE_MOCK:
    from dashboard_data_mock import (
        get_per_timeseries,
        get_income_latency_timeseries,
        get_roi_scenario,
        get_kpi_summary,
        get_regions,
    )
else:
    from dashboard_data_real import (
        get_per_timeseries,
        get_income_latency_timeseries,
        get_roi_scenario,
        get_kpi_summary,
        get_regions,
    )

__all__ = [
    "get_per_timeseries",
    "get_income_latency_timeseries",
    "get_roi_scenario",
    "get_kpi_summary",
    "get_regions",
]
