"""Minimal durable runner using the frozen scheduler and storage contracts."""

import asyncio
from collections.abc import AsyncIterator, Mapping
from typing import cast

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import (
    CodexEvent,
    CodexExecutionConfig,
    CodexTurnRef,
    EventType,
)
from codex_flow.domain.models import ExecutionMode, SandboxMode, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.runtime.backoff import sleep_backoff
from codex_flow.runtime.transient import is_transient_error
from codex_flow.scheduler.executor import command_completion_failed, terminal_status
from codex_flow.scheduler.graph import dependency_map, topological_order
from codex_flow.scheduler.locks import (
    GlobalConcurrencyLimiter,
    ThreadTurnLockManager,
    WorkspaceLockManager,
)
from codex_flow.scheduler.readiness import ready_task_ids
from codex_flow.storage.attempts import AttemptStarter
from codex_flow.storage.recovery import StartupReconciler
from codex_flow.storage.repositories import StorageRepositories
from codex_flow.storage.snapshots import create_run_snapshot


class DurableRunner:
    """Persist one deterministic workflow run without reimplementing DAG semantics."""

    def __init__(
        self, repository: StorageRepositories, adapter: CodexAdapter, *, max_concurrency: int = 1
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self._repository = repository
        self._adapter = adapter
        self._limiter = GlobalConcurrencyLimiter(max_concurrency)
        self._workspace_locks = WorkspaceLockManager()
        self._thread_locks = ThreadTurnLockManager()
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
            runnable: list[tuple[str, str]] = []
            for task_id in ready:
                if self._repository.get_workflow_run_paused(run_id):
                    break
                self._repository.update_task_run_state(
                    str(by_task[task_id]["id"]), TaskStatus.READY.value
                )
                runnable.append((str(by_task[task_id]["id"]), task_id))
            if not runnable:
                return
            await asyncio.gather(
                *(self._execute_task(task_run_id, tasks[task_id]) for task_run_id, task_id in runnable)
            )

    async def _execute_task(self, task_run_id: str, task: TaskDefinition) -> None:
        async with self._limiter.slot():
            if task.sandbox is SandboxMode.READ_ONLY:
                await self._execute_task_unlimited(task_run_id, task)
            else:
                async with self._workspace_locks.acquire_write(task.cwd):
                    await self._execute_task_unlimited(task_run_id, task)

    async def _execute_task_unlimited(self, task_run_id: str, task: TaskDefinition) -> None:
        for attempt_number in range(1, task.retry_policy.max_attempts + 1):
            if task.execution_mode is ExecutionMode.CONTINUE_THREAD:
                source_thread_id = self._continuation_source_thread_id(task_run_id, task)
                async with self._thread_locks.acquire_turn(source_thread_id):
                    transient = await self._execute_task_external(task_run_id, task)
            else:
                transient = await self._execute_task_external(task_run_id, task)
            if not transient or attempt_number == task.retry_policy.max_attempts:
                return
            self._repository.reset_task_for_retry(task_run_id)
            await sleep_backoff(attempt_number)
            self._repository.update_task_run_state(task_run_id, TaskStatus.READY.value)

    async def _execute_task_external(self, task_run_id: str, task: TaskDefinition) -> bool:
        config = CodexExecutionConfig(
            cwd=task.cwd,
            sandbox=task.sandbox,
            model=task.model,
            reasoning_effort=task.reasoning_effort,
            approval_mode=task.approval_mode,
        )
        if task.execution_mode is ExecutionMode.CONTINUE_THREAD:
            attempt_id, turn = await self._start_continuation_attempt(task_run_id, task)
        else:
            attempt_id, turn = await AttemptStarter(self._repository._connection, self._adapter).start(
                task_run_id, config, task.prompt
            )
        self._active_turns[task_run_id] = turn
        failed_command_observed = False
        turn_started = False
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
                    turn_started = True
                    if self._update_execution_state(
                        task_run_id, TaskStatus.RUNNING.value, turn.thread_id, turn.turn_id
                    ):
                        self._repository.update_attempt_state(attempt_id, TaskStatus.RUNNING.value)
                elif command_completion_failed(event):
                    failed_command_observed = True
                else:
                    status = terminal_status(event, failed_command_observed)
                    if status is not None:
                        if self._update_execution_state(
                            task_run_id, status.value, turn.thread_id, turn.turn_id
                        ):
                            self._repository.update_attempt_state(attempt_id, status.value)
                        return self._is_retryable_transport_event(event, turn_started)
            if self._update_execution_state(
                task_run_id, TaskStatus.FAILED.value, turn.thread_id, turn.turn_id
            ):
                self._repository.update_attempt_state(attempt_id, TaskStatus.FAILED.value)
            return False
        finally:
            self._active_turns.pop(task_run_id, None)

    @staticmethod
    def _is_transient_event(event: CodexEvent) -> bool:
        """Recognize only explicit transient signals attached to an event."""
        return any(
            is_transient_error(event.details.get(key))
            for key in ("code", "error_code", "signal", "type")
        )

    @classmethod
    def _is_retryable_transport_event(cls, event: CodexEvent, turn_started: bool) -> bool:
        """Retry only an explicit transport failure seen before turn start."""
        if event.event_type is EventType.ATTENTION_REQUIRED:
            return cls._is_transient_event(event)
        return event.event_type is EventType.TRANSPORT_ERROR and not turn_started and cls._is_transient_event(event)

    async def _start_continuation_attempt(
        self, task_run_id: str, task: TaskDefinition
    ) -> tuple[str, CodexTurnRef]:
        """Resume the explicit successful source thread for a continuation task."""
        source_thread_id = self._continuation_source_thread_id(task_run_id, task)
        return await AttemptStarter(self._repository._connection, self._adapter).start_continuation(
            task_run_id, source_thread_id, task.prompt
        )

    def _continuation_source_thread_id(self, task_run_id: str, task: TaskDefinition) -> str:
        source_id = task.continue_from_task_id
        if source_id is None:
            raise ValueError("continue_from_task_id is required")
        task_row = self._repository.get_task_run(task_run_id)
        if task_row is None:
            raise ValueError(f"task run not found: {task_run_id}")
        source = next(
            (
                row
                for row in self._repository.load_task_runs(str(task_row["workflow_run_id"]))
                if str(row["task_id"]) == source_id
            ),
            None,
        )
        if source is None:
            raise ValueError(f"continuation source does not exist: {source_id}")
        if str(source["status"]) != TaskStatus.SUCCESS.value:
            raise ValueError("continuation source must be SUCCESS")
        source_thread_id = source["thread_id"]
        if not isinstance(source_thread_id, str) or not source_thread_id:
            raise ValueError("continuation source has no thread_id")
        return source_thread_id

    def _update_execution_state(
        self, task_run_id: str, status: str, thread_id: str, turn_id: str
    ) -> bool:
        for expected_status in (TaskStatus.STARTING.value, TaskStatus.RUNNING.value):
            if self._repository.compare_and_update_task_run_state(
                task_run_id, expected_status, status, thread_id, turn_id
            ):
                return True
        return False

    def _finish_run(self, run_id: str, statuses: Mapping[str, TaskStatus]) -> None:
        if all(status is TaskStatus.SUCCESS for status in statuses.values()):
            self._repository.update_workflow_run_state(run_id, TaskStatus.SUCCESS.value)
        elif all(status not in {TaskStatus.PENDING, TaskStatus.READY, TaskStatus.STARTING, TaskStatus.RUNNING} for status in statuses.values()):
            self._repository.update_workflow_run_state(run_id, TaskStatus.FAILED.value)
