"""Transactional repositories for the frozen early-phase storage schema."""

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from codex_flow.application.control_contract import ControlResult
from codex_flow.domain.models import WorkflowDefinition


def _now() -> str:
    return datetime.now(UTC).isoformat()


_RETRYABLE_TASK_STATUSES = frozenset({"FAILED", "INTERRUPTED", "NEEDS_ATTENTION"})


class StorageRepositories:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save_workflow_definition(self, workflow: WorkflowDefinition) -> None:
        payload = workflow.model_dump_json()
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO workflows(id, name, definition_json, created_at) VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name, definition_json = excluded.definition_json
                """,
                (workflow.id, workflow.name, payload, _now()),
            )
            self._connection.execute("DELETE FROM edges WHERE workflow_id = ?", (workflow.id,))
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

    def list_workflows(self) -> list[sqlite3.Row]:
        return list(self._connection.execute("SELECT * FROM workflows ORDER BY id"))

    def get_workflow_run(self, workflow_run_id: str) -> sqlite3.Row | None:
        return cast(
            sqlite3.Row | None,
            self._connection.execute(
                "SELECT * FROM workflow_runs WHERE id = ?", (workflow_run_id,)
            ).fetchone(),
        )

    def list_workflow_runs(self, workflow_id: str | None = None) -> list[sqlite3.Row]:
        if workflow_id is None:
            return list(self._connection.execute("SELECT * FROM workflow_runs ORDER BY created_at, id"))
        return list(
            self._connection.execute(
                "SELECT * FROM workflow_runs WHERE workflow_id = ? ORDER BY created_at, id",
                (workflow_id,),
            )
        )

    def create_workflow_run(self, workflow_id: str, snapshot: dict[str, object]) -> str:
        run_id = str(uuid4())
        with self._connection:
            self._connection.execute(
                "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, workflow_id, json.dumps(snapshot, sort_keys=True), "PENDING", _now()),
            )
        return run_id

    def get_workflow_run_paused(self, workflow_run_id: str) -> bool:
        """Read the durable pause flag, failing closed for an unknown run."""
        row = self._connection.execute(
            "SELECT paused FROM workflow_runs WHERE id = ?", (workflow_run_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"workflow run not found: {workflow_run_id}")
        return bool(row["paused"])

    def set_workflow_run_paused(self, workflow_run_id: str, paused: bool) -> None:
        """Persist pause state and metadata in one transaction."""
        paused_at = _now() if paused else None
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE workflow_runs SET paused = ?, paused_at = ? WHERE id = ?",
                (int(paused), paused_at, workflow_run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"workflow run not found: {workflow_run_id}")

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

    def compare_and_update_task_run_state(
        self,
        task_run_id: str,
        expected_status: str,
        status: str,
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> bool:
        """Update a task only when its observed state still matches the expected state."""
        with self._connection:
            if thread_id is None and turn_id is None:
                cursor = self._connection.execute(
                    "UPDATE task_runs SET status = ? WHERE id = ? AND status = ?",
                    (status, task_run_id, expected_status),
                )
            else:
                cursor = self._connection.execute(
                    """
                    UPDATE task_runs
                    SET status = ?, thread_id = ?, turn_id = ?
                    WHERE id = ? AND status = ?
                    """,
                    (status, thread_id, turn_id, task_run_id, expected_status),
                )
            return cursor.rowcount == 1

    def reset_task_for_retry(self, task_run_id: str) -> str:
        """Reset one retryable task and audit it atomically without creating an attempt."""
        row = self._connection.execute(
            "SELECT workflow_run_id, task_id, status FROM task_runs WHERE id = ?",
            (task_run_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"task run not found: {task_run_id}")
        previous_status = str(row["status"])
        if previous_status not in _RETRYABLE_TASK_STATUSES:
            raise ValueError(f"retry reset is not allowed from {previous_status}")

        event_id = str(uuid4())
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE task_runs
                SET status = 'PENDING', thread_id = NULL, turn_id = NULL
                WHERE id = ? AND status = ?
                """,
                (task_run_id, previous_status),
            )
            if cursor.rowcount != 1:
                raise ValueError("task run changed before retry reset")
            self._connection.execute(
                """
                INSERT INTO events(
                    id, workflow_run_id, task_run_id, event_type, payload_json, created_at
                ) VALUES (?, ?, ?, 'RETRY_REQUESTED', ?, ?)
                """,
                (
                    event_id,
                    row["workflow_run_id"],
                    task_run_id,
                    json.dumps(
                        {
                            "previous_status": previous_status,
                            "task_id": row["task_id"],
                            "target_status": "PENDING",
                        },
                        sort_keys=True,
                    ),
                    _now(),
                ),
            )
        return event_id

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

    def append_manual_action_audit(
        self, result: ControlResult, *, task_run_id: str | None = None
    ) -> str:
        """Append a credential-free audit event for an accepted or rejected control."""
        payload: dict[str, object] = {
            "run_id": result.run_id,
            "task_id": result.task_id,
            "action": result.action.value,
            "accepted": result.accepted,
            "previous_status": (
                result.previous_status.value if result.previous_status is not None else None
            ),
            "target_status": result.status.value if result.status is not None else None,
            "retry_requested": result.retry_requested,
        }
        if result.error_code is not None:
            payload["error_code"] = result.error_code
        if result.message is not None:
            payload["message"] = result.message
        event_type = "MANUAL_ACTION_ACCEPTED" if result.accepted else "MANUAL_ACTION_REJECTED"
        return self.append_event(
            event_type,
            payload,
            workflow_run_id=result.run_id,
            task_run_id=task_run_id,
        )

    def load_active_runs(self) -> list[sqlite3.Row]:
        return list(self._connection.execute("SELECT * FROM workflow_runs WHERE status NOT IN ('SUCCESS', 'FAILED', 'CANCELLED')"))

    def load_active_runs_for_workflow(self, workflow_id: str) -> list[sqlite3.Row]:
        return list(
            self._connection.execute(
                "SELECT * FROM workflow_runs WHERE workflow_id = ? AND status NOT IN ('SUCCESS', 'FAILED', 'CANCELLED')",
                (workflow_id,),
            )
        )

    def load_task_runs(self, workflow_run_id: str) -> list[sqlite3.Row]:
        return list(
            self._connection.execute(
                "SELECT * FROM task_runs WHERE workflow_run_id = ? ORDER BY created_at, id",
                (workflow_run_id,),
            )
        )

    def get_task_run(self, task_run_id: str) -> sqlite3.Row | None:
        return cast(
            sqlite3.Row | None,
            self._connection.execute(
                "SELECT * FROM task_runs WHERE id = ?", (task_run_id,)
            ).fetchone(),
        )

    def update_workflow_run_state(self, workflow_run_id: str, status: str) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE workflow_runs SET status = ? WHERE id = ?", (status, workflow_run_id)
            )

    def update_attempt_state(self, attempt_id: str, status: str) -> None:
        with self._connection:
            self._connection.execute("UPDATE attempts SET status = ? WHERE id = ?", (status, attempt_id))

    def load_attempts(self, task_run_id: str) -> list[sqlite3.Row]:
        return list(self._connection.execute("SELECT * FROM attempts WHERE task_run_id = ? ORDER BY created_at, id", (task_run_id,)))

    def load_events_for_run(self, workflow_run_id: str) -> list[sqlite3.Row]:
        return list(
            self._connection.execute(
                "SELECT * FROM events WHERE workflow_run_id = ? ORDER BY rowid",
                (workflow_run_id,),
            )
        )

    def load_events_after(self, workflow_run_id: str, event_id: str) -> list[sqlite3.Row]:
        cursor = self._connection.execute(
            "SELECT rowid FROM events WHERE workflow_run_id = ? AND id = ?",
            (workflow_run_id, event_id),
        ).fetchone()
        if cursor is None:
            raise ValueError("event cursor not found")
        return list(
            self._connection.execute(
                "SELECT * FROM events WHERE workflow_run_id = ? AND rowid > ? ORDER BY rowid",
                (workflow_run_id, cursor["rowid"]),
            )
        )
