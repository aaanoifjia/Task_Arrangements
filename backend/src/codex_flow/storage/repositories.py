"""Transactional repositories for the frozen early-phase storage schema."""

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import uuid4

from codex_flow.domain.models import WorkflowDefinition


def _now() -> str:
    return datetime.now(UTC).isoformat()


class StorageRepositories:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save_workflow_definition(self, workflow: WorkflowDefinition) -> None:
        payload = workflow.model_dump_json()
        with self._connection:
            self._connection.execute(
                "INSERT OR REPLACE INTO workflows(id, name, definition_json, created_at) VALUES (?, ?, ?, ?)",
                (workflow.id, workflow.name, payload, _now()),
            )
            self._connection.execute("DELETE FROM tasks WHERE workflow_id = ?", (workflow.id,))
            for task in workflow.tasks:
                self._connection.execute(
                    "INSERT INTO tasks(workflow_id, id, definition_json) VALUES (?, ?, ?)",
                    (workflow.id, task.id, task.model_dump_json()),
                )
            for edge in workflow.edges:
                self._connection.execute(
                    "INSERT INTO edges(workflow_id, source_task_id, target_task_id) VALUES (?, ?, ?)",
                    (workflow.id, edge.source_task_id, edge.target_task_id),
                )

    def load_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        row = self._connection.execute(
            "SELECT definition_json FROM workflows WHERE id = ?", (workflow_id,)
        ).fetchone()
        return None if row is None else WorkflowDefinition.model_validate_json(row["definition_json"])

    def create_workflow_run(self, workflow_id: str, snapshot: dict[str, object]) -> str:
        run_id = str(uuid4())
        with self._connection:
            self._connection.execute(
                "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, workflow_id, json.dumps(snapshot, sort_keys=True), "PENDING", _now()),
            )
        return run_id

    def create_task_runs(self, workflow_run_id: str, task_ids: Iterable[str]) -> list[str]:
        task_ids = list(task_ids)
        task_run_ids = [str(uuid4()) for _ in task_ids]
        with self._connection:
            self._connection.executemany(
                "INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
                [(run_id, workflow_run_id, task_id, "PENDING", _now()) for run_id, task_id in zip(task_run_ids, task_ids, strict=True)],
            )
        return task_run_ids

    def create_attempt(self, task_run_id: str, status: str = "STARTING") -> str:
        attempt_id = str(uuid4())
        with self._connection:
            self._connection.execute(
                "INSERT INTO attempts(id, task_run_id, status, created_at) VALUES (?, ?, ?, ?)",
                (attempt_id, task_run_id, status, _now()),
            )
        return attempt_id

    def update_task_run_state(
        self, task_run_id: str, status: str, thread_id: str | None = None, turn_id: str | None = None
    ) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE task_runs SET status = ?, thread_id = ?, turn_id = ? WHERE id = ?",
                (status, thread_id, turn_id, task_run_id),
            )

    def append_event(
        self, event_type: str, payload: dict[str, object], *, workflow_run_id: str | None = None,
        task_run_id: str | None = None, attempt_id: str | None = None
    ) -> str:
        event_id = str(uuid4())
        with self._connection:
            self._connection.execute(
                "INSERT INTO events(id, workflow_run_id, task_run_id, attempt_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event_id, workflow_run_id, task_run_id, attempt_id, event_type, json.dumps(payload, sort_keys=True), _now()),
            )
        return event_id

    def load_active_runs(self) -> list[sqlite3.Row]:
        return list(self._connection.execute("SELECT * FROM workflow_runs WHERE status NOT IN ('SUCCESS', 'FAILED', 'CANCELLED')"))

    def load_attempts(self, task_run_id: str) -> list[sqlite3.Row]:
        return list(self._connection.execute("SELECT * FROM attempts WHERE task_run_id = ? ORDER BY created_at, id", (task_run_id,)))
