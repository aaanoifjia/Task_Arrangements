"""Minimal durable runner using the frozen scheduler and storage contracts."""

from collections.abc import AsyncIterator, Mapping
from typing import cast

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import (
    CodexEvent,
    CodexExecutionConfig,
    CodexTurnRef,
    EventType,
)
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.executor import command_completion_failed, terminal_status
from codex_flow.scheduler.graph import dependency_map, topological_order
from codex_flow.scheduler.readiness import ready_task_ids
from codex_flow.storage.attempts import AttemptStarter
from codex_flow.storage.recovery import StartupReconciler
from codex_flow.storage.repositories import StorageRepositories
from codex_flow.storage.snapshots import create_run_snapshot


class DurableRunner:
    """Persist one deterministic workflow run without reimplementing DAG semantics."""

    def __init__(self, repository: StorageRepositories, adapter: CodexAdapter) -> None:
        self._repository = repository
        self._adapter = adapter
        self._active_turns: dict[str, CodexTurnRef] = {}

    def active_turn(self, task_run_id: str) -> CodexTurnRef | None:
        """Return the in-memory turn currently executing for a task run."""
        return self._active_turns.get(task_run_id)

    @property
    def active_turns(self) -> dict[str, CodexTurnRef]:
        """Return a snapshot of active turns without exposing mutable registry state."""
        return dict(self._active_turns)

    async def run(self, workflow: WorkflowDefinition) -> str:
        order = topological_order(workflow)
        active_runs = self._repository.load_active_runs_for_workflow(workflow.id)
        if len(active_runs) > 1:
            raise ValueError(f"more than one active run exists for workflow: {workflow.id}")
        if active_runs:
            await StartupReconciler(self._repository._connection, self._adapter).reconcile()
            return str(active_runs[0]["id"])

        run_id = self.prepare_run(workflow, order)
        await self.execute_run(run_id, workflow)
        return run_id

    def prepare_run(self, workflow: WorkflowDefinition, order: list[str] | None = None) -> str:
        """Persist a new run and its task rows before background execution starts."""
        active_runs = self._repository.load_active_runs_for_workflow(workflow.id)
        if active_runs:
            raise ValueError(f"an active run already exists for workflow: {workflow.id}")
        task_order = order or topological_order(workflow)
        self._repository.save_workflow_definition(workflow)
        run_id = self._repository.create_workflow_run(workflow.id, create_run_snapshot(workflow))
        self._repository.create_task_runs(run_id, task_order)
        self._repository.update_workflow_run_state(run_id, "RUNNING")
        return run_id

    async def execute_run(self, run_id: str, workflow: WorkflowDefinition) -> None:
        dependencies = dependency_map(workflow)
        tasks = {task.id: task for task in workflow.tasks}
        while True:
            rows = self._repository.load_task_runs(run_id)
            by_task = {str(row["task_id"]): row for row in rows}
            statuses = {task_id: TaskStatus(str(row["status"])) for task_id, row in by_task.items()}
            for task_id in topological_order(workflow):
                if statuses[task_id] is TaskStatus.PENDING and any(
                    statuses[parent] is not TaskStatus.SUCCESS for parent in dependencies[task_id]
                ):
                    self._repository.update_task_run_state(str(by_task[task_id]["id"]), TaskStatus.BLOCKED.value)
                    statuses[task_id] = TaskStatus.BLOCKED
            ready = ready_task_ids(workflow, statuses)
            if not ready:
                self._finish_run(run_id, statuses)
                return
            for task_id in ready:
                self._repository.update_task_run_state(
                    str(by_task[task_id]["id"]), TaskStatus.READY.value
                )
                await self._execute_task(str(by_task[task_id]["id"]), tasks[task_id])

    async def _execute_task(self, task_run_id: str, task: TaskDefinition) -> None:
        config = CodexExecutionConfig(
            cwd=task.cwd,
            sandbox=task.sandbox,
            model=task.model,
            reasoning_effort=task.reasoning_effort,
            approval_mode=task.approval_mode,
        )
        attempt_id, turn = await AttemptStarter(self._repository._connection, self._adapter).start(
            task_run_id, config, task.prompt
        )
        self._active_turns[task_run_id] = turn
        failed_command_observed = False
        try:
            stream = cast("AsyncIterator[CodexEvent]", self._adapter.stream_turn(turn))
            async for event in stream:
                self._repository.append_event(
                    event.event_type.value,
                    event.details,
                    task_run_id=task_run_id,
                    attempt_id=attempt_id,
                )
                if event.event_type is EventType.TURN_STARTED:
                    self._repository.update_task_run_state(task_run_id, TaskStatus.RUNNING.value, turn.thread_id, turn.turn_id)
                    self._repository.update_attempt_state(attempt_id, TaskStatus.RUNNING.value)
                elif command_completion_failed(event):
                    failed_command_observed = True
                else:
                    status = terminal_status(event, failed_command_observed)
                    if status is not None:
                        self._repository.update_task_run_state(task_run_id, status.value, turn.thread_id, turn.turn_id)
                        self._repository.update_attempt_state(attempt_id, status.value)
                        return
            self._repository.update_task_run_state(task_run_id, TaskStatus.FAILED.value, turn.thread_id, turn.turn_id)
            self._repository.update_attempt_state(attempt_id, TaskStatus.FAILED.value)
        finally:
            self._active_turns.pop(task_run_id, None)

    def _finish_run(self, run_id: str, statuses: Mapping[str, TaskStatus]) -> None:
        if all(status is TaskStatus.SUCCESS for status in statuses.values()):
            self._repository.update_workflow_run_state(run_id, TaskStatus.SUCCESS.value)
        elif all(status not in {TaskStatus.PENDING, TaskStatus.READY, TaskStatus.STARTING, TaskStatus.RUNNING} for status in statuses.values()):
            self._repository.update_workflow_run_state(run_id, TaskStatus.FAILED.value)
