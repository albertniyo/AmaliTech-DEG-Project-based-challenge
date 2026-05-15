import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

class MonitorStore:
    """In‑memory store for monitor records with optional JSON persistence."""

    def __init__(self, file_path: str = "monitors.json"):
        self.file_path = file_path
        self._monitors: Dict[str, dict] = {}
        self._lock = asyncio.Lock()   # prevent race conditions
        self._load_from_file()

    # persistence helpers
    def _load_from_file(self):
        """Load monitors from JSON file if it exists."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    data = json.load(f)
                # convert from raw dict to internal format - json
                for mid, mdata in data.items():
                    mdata["task"] = None  # tasks can't be serialized
                    mdata.setdefault("status", "active")
                    mdata.setdefault("alert_email", None)
                    mdata.setdefault("timeout", 60)
                    self._monitors[mid] = mdata
            except Exception as e:
                print(f"Error loading monitors file: {e}")

    async def _save_to_file(self):
        """Persist current state to JSON (without task handles)."""
        async with self._lock:
            # safe copy without asyncio.Task objects
            to_save = {}
            for mid, mdata in self._monitors.items():
                to_save[mid] = {
                    "id": mdata["id"],
                    "timeout": mdata["timeout"],
                    "status": mdata["status"],
                    "alert_email": mdata["alert_email"],
                    # don't save "task"
                }
            try:
                with open(self.file_path, "w") as f:
                    json.dump(to_save, f, indent=2)
            except Exception as e:
                print(f"Error saving monitors file: {e}")

    # public CRUD methods
    async def create(self, monitor_id: str, timeout: int, alert_email: Optional[str] = None) -> dict:
        async with self._lock:
            if monitor_id in self._monitors:
                return None  # already exists
            monitor = {
                "id": monitor_id,
                "timeout": timeout,
                "status": "active",
                "alert_email": alert_email,
                "task": None,
            }
            self._monitors[monitor_id] = monitor
        await self._save_to_file()
        return monitor

    async def update_status(self, monitor_id: str, new_status: str) -> bool:
        async with self._lock:
            monitor = self._monitors.get(monitor_id)
            if not monitor:
                return False
            monitor["status"] = new_status
        await self._save_to_file()
        return True

    async def delete(self, monitor_id: str) -> bool:
        async with self._lock:
            if monitor_id not in self._monitors:
                return False
            del self._monitors[monitor_id]
        await self._save_to_file()
        return True

    # task management (just in‑memory, not persisted)
    def set_task(self, monitor_id: str, task: asyncio.Task) -> bool:
        """Attach an asyncio Task to a monitor."""
        monitor = self._monitors.get(monitor_id)
        if monitor:
            monitor["task"] = task
            return True
        return False

    def cancel_task(self, monitor_id: str):
        """Cancel and remove the timer task for a monitor."""
        monitor = self._monitors.get(monitor_id)
        if monitor and monitor["task"]:
            monitor["task"].cancel()
            monitor["task"] = None

store = MonitorStore()