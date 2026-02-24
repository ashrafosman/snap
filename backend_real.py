"""
Real backend — connect to SQL warehouse or Lakebase.
Set USE_MOCK_BACKEND=false and add app resources (warehouse/Lakebase) in app.yaml.
"""
import os
from databricks.sdk.core import Config
from databricks import sql

# Example: SQL warehouse. For Lakebase use psycopg2 + PGHOST/PGPASSWORD from valueFrom.
def _get_conn():
    cfg = Config()
    wh_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not wh_id:
        raise RuntimeError("DATABRICKS_WAREHOUSE_ID not set. Add SQL warehouse resource in app.yaml.")
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{wh_id}",
        credentials_provider=lambda: cfg.authenticate,
    )


class RealBackend:
    """Implement get_tasks, get_stats, add_task, complete_task using SQL or Lakebase."""

    def get_tasks(self):
        # TODO: SELECT from your table
        return []

    def get_stats(self):
        # TODO: COUNT by status
        return {"total": 0, "pending": 0, "completed": 0}

    def add_task(self, title: str, description: str | None = None):
        # TODO: INSERT
        pass

    def complete_task(self, task_id: str):
        # TODO: UPDATE status
        pass
