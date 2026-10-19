"""Durable event and task-state query service."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codex_flow.api.schemas import EventView, TaskRunView

from codex_flow.storage.repositories import StorageRepositories


class EventApplicationService:
    def __init__(self, repository: StorageRepositories) -> None:
        self._repository = repository

    def list_events(self, run_id: str, after_event_id: str | None = None) -> list[EventView]:
        from codex_flow.api.schemas import EventView

        rows = (
            self._repository.load_events_for_run(run_id)
            if after_event_id is None
            else self._repository.load_events_after(run_id, after_event_id)
        )
        return [
            EventView(
                id=row["id"],
                workflow_run_id=row["workflow_run_id"],
                task_run_id=row["task_run_id"],
                attempt_id=row["attempt_id"],
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def task_snapshot(self, run_id: str) -> list[TaskRunView]:
        from codex_flow.api.schemas import TaskRunView

        return [TaskRunView(**dict(row)) for row in self._repository.load_task_runs(run_id)]

    def run_is_terminal(self, run_id: str) -> bool:
        row = self._repository.get_workflow_run(run_id)
        return row is not None and row["status"] in {"SUCCESS", "FAILED", "CANCELLED"}
