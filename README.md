# Executive Fiscal ROI Dashboard

Streamlit **Databricks App** that tracks SNAP Payment Error Rate (PER) trends, income verification latency by region, and an ROI scenario simulator for remediation strategies.

## Features

- **PER trend** — Line chart with federal 6% threshold
- **Wage ingestion latency** — Median and P90 with markers for **2025-12-03** (ingestion change) and **2026-01-12** (remediation)
- **Scenario simulator** — Target PER slider (e.g. 5.8% by 2026-03), projected penalty exposure
- **Region breakdown** — Selector for All / regions
- **Dark theme** — Matches Executive Dashboard style

## Data sources (Unity Catalog)

| Table | Use |
|-------|-----|
| `gold_snap_per_timeseries` | month_start, region, per_rate, overpayment_usd, issued_benefits_usd |
| `gold_snap_roi_scenarios` | per_rate_projected, projected_penalty_exposure_usd (by target PER) |
| `gold_income_latency_timeseries` | month_start, region, median_latency_days, p90_latency_days |

**Default:** `ashraf.ashraf_osman_snap2`. Override with `SNAP_CATALOG` and `SNAP_SCHEMA` if needed.

## Run locally

```bash
cd /path/to/SNAP
pip install -r requirements.txt
streamlit run app.py
```

Uses **mock** data by default (`USE_MOCK_BACKEND=true`). Open http://localhost:8501.

## Deploy to Databricks

1. Add a **SQL warehouse** as an app resource in the workspace.
2. In `app.yaml`, set env:
   - `DATABRICKS_WAREHOUSE_ID`: valueFrom workspaceConfig (SQL warehouse)
   - `USE_MOCK_BACKEND`: `"false"`
3. Sync and deploy:
   ```bash
   databricks sync . /Workspace/snap --profile <profile>
   databricks apps deploy snap --source-code-path /Workspace/snap --profile <profile>
   ```

## Project layout

| File | Purpose |
|------|--------|
| `app.py` | Dashboard UI (KPIs, charts, scenario slider) |
| `dashboard_data.py` | Data layer entry (mock vs real) |
| `dashboard_data_mock.py` | Synthetic time series for local dev |
| `dashboard_data_real.py` | Queries gold_* tables via SQL warehouse |
| `app.yaml` | Databricks Apps config |
| `.streamlit/config.toml` | Dark theme, port 8080 |

## Links

- [Databricks Apps](https://docs.databricks.com/dev-tools/databricks-apps/)
- [Apps Cookbook](https://apps-cookbook.dev/)
