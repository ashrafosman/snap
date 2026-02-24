"""
Mock backend for local development — no Databricks resources required.
Replace with backend_real.py when deploying (SQL warehouse or Lakebase).
"""
from datetime import datetime

# In-memory store (resets on restart)
_tasks = [
    {"id": "1", "title": "Set up Databricks workspace", "description": "Create cluster and SQL warehouse", "status": "pending", "created_at": "2025-02-24T10:00:00"},
    {"id": "2", "title": "Deploy SNAP app", "description": "Deploy via CLI or Asset Bundles", "status": "pending", "created_at": "2025-02-24T10:05:00"},
    {"id": "3", "title": "Connect real backend", "description": "Wire to Lakebase or SQL warehouse", "status": "completed", "created_at": "2025-02-24T09:00:00"},
]
_next_id = 4


class MockBackend:
    def get_tasks(self):
        return list(_tasks)

    def get_stats(self):
        total = len(_tasks)
        pending = sum(1 for t in _tasks if t.get("status") == "pending")
        return {"total": total, "pending": pending, "completed": total - pending}

    def add_task(self, title: str, description: str | None = None):
        global _tasks, _next_id
        _tasks.append({
            "id": str(_next_id),
            "title": title,
            "description": description or "",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
        })
        _next_id += 1

    def complete_task(self, task_id: str):
        for t in _tasks:
            if t["id"] == task_id:
                t["status"] = "completed"
                break
