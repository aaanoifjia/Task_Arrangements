"""Fail-closed reconciliation of interrupted local task runs."""

import json
import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import CodexThreadRef


def _now() -> str:
    return datetime.now(UTC).isoformat()


class StartupReconciler:
    def __init__(self, connection: sqlite3.Connection, adapter: CodexAdapter) -> None:
        self._connection = connection
        self._adapter = adapter

    async def reconcile(self) -> list[str]:
        rows = self._connection.execute(
            "SELECT id, thread_id, status FROM task_runs WHERE status IN ('STARTING', 'RUNNING', 'NEEDS_ATTENTION')"
        ).fetchall()
        reconciled: list[str] = []
        for row in rows:
            if row["thread_id"] is None:
                self._set_state(row["id"], "FAILED", "RECOVERY_REQUIRED_NO_THREAD")
            else:
                try:
                    await self._adapter.read_thread(CodexThreadRef(thread_id=row["thread_id"]))
                except Exception:  # noqa: BLE001 - unknown external state fails closed.
                    self._set_state(row["id"], "FAILED", "RECOVERY_READ_FAILED")
                else:
                    self._set_state(row["id"], "NEEDS_ATTENTION", "RECOVERY_THREAD_REQUIRES_RECONCILIATION")
            reconciled.append(row["id"])
        return reconciled

    def _set_state(self, task_run_id: str, status: str, event_type: str) -> None:
        with self._connection:
            self._connection.execute("UPDATE task_runs SET status = ? WHERE id = ?", (status, task_run_id))
            self._connection.execute(
                "INSERT INTO events(id, task_run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid4()), task_run_id, event_type, json.dumps({"recovered": True}), _now()),
            )
