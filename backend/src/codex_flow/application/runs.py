"""Application service for durable workflow runs and task history."""

import json
from typing import Any

from codex_flow.api.schemas import (
    AttemptView,
    RunDetail,
    RunHistoryPage,
    RunStartResponse,
    RunSummary,
    TaskRunView,
)
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.repositories import StorageRepositories


class RunServiceError(ValueError):
    """Base error for run service failures."""


class RunNotFoundError(RunServiceError):
    pass


class RunWorkflowNotFoundError(RunServiceError):
    pass


class ActiveRunConflictError(RunServiceError):
    pass


class RunApplicationService:
    def __init__(self, repository: StorageRepositories, runtime: RuntimeManager) -> None:
        self._repository = repository
        self._runtime = runtime

    async def start_workflow(self, workflow_id: str) -> RunStartResponse:
        workflow = self._repository.load_workflow(workflow_id)
        if workflow is None:
            raise RunWorkflowNotFoundError(f"workflow not found: {workflow_id}")
        try:
            return RunStartResponse(run_id=await self._runtime.start(workflow))
        except ValueError as error:
            raise ActiveRunConflictError(str(error)) from error

    def list_runs(self, workflow_id: str | None = None) -> list[RunSummary]:
        return [self._summary(row) for row in self._repository.list_workflow_runs(workflow_id)]

    def list_runs_page(
        self,
        workflow_id: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> RunHistoryPage:
        rows, next_cursor = self._repository.list_workflow_runs_page(workflow_id, cursor, limit)
        return RunHistoryPage(
            items=[self._summary(row) for row in rows],
            next_cursor=next_cursor,
        )

    def get_run(self, run_id: str) -> RunDetail:
        row = self._repository.get_workflow_run(run_id)
        if row is None:
            raise RunNotFoundError(f"run not found: {run_id}")
        return RunDetail(
            **self._summary(row).model_dump(),
            snapshot=json.loads(row["snapshot_json"]),
        )

    def list_task_runs(self, run_id: str) -> list[TaskRunView]:
        self._require_run(run_id)
        return [TaskRunView(**dict(row)) for row in self._repository.load_task_runs(run_id)]

    def get_task_run(self, run_id: str, task_run_id: str) -> TaskRunView:
        self._require_run(run_id)
        row = self._repository.get_task_run(task_run_id)
        if row is None or row["workflow_run_id"] != run_id:
            raise RunNotFoundError(f"task run not found: {task_run_id}")
        return TaskRunView(**dict(row))

    def list_attempts(self, run_id: str, task_run_id: str) -> list[AttemptView]:
        self.get_task_run(run_id, task_run_id)
        return [AttemptView(**dict(row)) for row in self._repository.load_attempts(task_run_id)]

    @staticmethod
    def _summary(row: Any) -> RunSummary:
        return RunSummary(
            id=row["id"],
            workflow_id=row["workflow_id"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def _require_run(self, run_id: str) -> None:
        if self._repository.get_workflow_run(run_id) is None:
            raise RunNotFoundError(f"run not found: {run_id}")
