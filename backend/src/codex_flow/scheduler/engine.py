"""Deterministic asynchronous scheduler for a workflow definition."""

import asyncio
from collections.abc import Mapping
from contextvars import ContextVar
from typing import cast

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import (
    CodexExecutionConfig,
    CodexThreadRef,
    CodexThreadSnapshot,
    CodexTurnOutcome,
    CodexTurnRef,
)
from codex_flow.domain.models import ExecutionMode, TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.actions import ManualActionError, SchedulerActions
from codex_flow.scheduler.continuation import (
    ContinuationExecutionResult,
    ContinuationSource,
    ThreadContinuation,
)
from codex_flow.scheduler.executor import ExecutionResult, TaskExecutor
from codex_flow.scheduler.graph import dependency_map, topological_order
from codex_flow.scheduler.locks import (
    GlobalConcurrencyLimiter,
    ThreadTurnLockManager,
    WorkspaceLockManager,
)
from codex_flow.scheduler.readiness import ready_task_ids
from codex_flow.scheduler.state_machine import TransitionTrigger, transition

_task_context: ContextVar[str | None] = ContextVar("scheduler_task_id", default=None)


class _RecordingAdapter:
    """Record adapter references without exposing SDK details to the scheduler."""

    def __init__(self, delegate: CodexAdapter, thread_ids: dict[str, str], turn_ids: dict[str, str]) -> None:
        self._delegate = delegate
        self._thread_ids = thread_ids
        self._turn_ids = turn_ids

    async def create_thread(self, config: CodexExecutionConfig) -> CodexThreadRef:
        thread = await self._delegate.create_thread(config)
        if task_id := _task_context.get():
            self._thread_ids[task_id] = thread.thread_id
        return thread

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef:
        return await self._delegate.resume_thread(thread)

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        turn = await self._delegate.start_turn(thread, prompt)
        if task_id := _task_context.get():
            self._turn_ids[task_id] = turn.turn_id
            self._thread_ids[task_id] = turn.thread_id
        return turn

    def stream_turn(self, turn: CodexTurnRef):  # type: ignore[no-untyped-def]
        return self._delegate.stream_turn(turn)

    async def interrupt_turn(self, turn: CodexTurnRef) -> CodexTurnOutcome:
        return await self._delegate.interrupt_turn(turn)

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot:
        return await self._delegate.read_thread(thread)

    async def set_thread_name(self, thread: CodexThreadRef, name: str) -> None:
        await self._delegate.set_thread_name(thread, name)

    async def close(self) -> None:
        await self._delegate.close()


class AsyncScheduler:
    """Execute ready tasks in deterministic topological order."""

    def __init__(
        self,
        workflow: WorkflowDefinition,
        adapter: CodexAdapter,
        *,
        max_concurrency: int = 1,
        statuses: Mapping[str, TaskStatus] | None = None,
    ) -> None:
        self._workflow = workflow
        self._tasks = {task.id: task for task in workflow.tasks}
        self._dependencies = dependency_map(workflow)
        self._order = topological_order(workflow)
        self.statuses = self._initial_statuses(statuses)
        self.thread_ids: dict[str, str] = {}
        self.turn_ids: dict[str, str] = {}
        self._retry_requests: set[str] = set()
        self._attempt_counts = {task_id: 0 for task_id in self._order}
        self.actions = SchedulerActions(self.statuses, self._request_retry)
        self._limiter = GlobalConcurrencyLimiter(max_concurrency)
        self._workspace_locks = WorkspaceLockManager()
        self._thread_locks = ThreadTurnLockManager()
        self._adapter = _RecordingAdapter(adapter, self.thread_ids, self.turn_ids)
        self._executor = TaskExecutor(
            cast(CodexAdapter, self._adapter),
            self._limiter,
            self._workspace_locks,
            self._thread_locks,
        )
        self._continuation = ThreadContinuation(cast(CodexAdapter, self._adapter))

    def _initial_statuses(self, supplied: Mapping[str, TaskStatus] | None) -> dict[str, TaskStatus]:
        if supplied is None:
            return {task_id: TaskStatus.PENDING for task_id in self._order}
        unexpected = set(supplied) - set(self._order)
        missing = set(self._order) - set(supplied)
        if unexpected or missing:
            raise ValueError("statuses must contain exactly the workflow task ids")
        return dict(supplied)

    def recalculate_readiness(self) -> list[str]:
        """Propagate dependency failures, then return ready tasks in fixed order."""
        for task_id in self._order:
            status = self.statuses[task_id]
            dependency_statuses = [self.statuses[item] for item in self._dependencies[task_id]]
            if status is TaskStatus.PENDING and any(
                item is not TaskStatus.SUCCESS for item in dependency_statuses
            ):
                self.statuses[task_id] = transition(
                    status, TaskStatus.BLOCKED, TransitionTrigger.DEPENDENCY_EVALUATION
                )

        ready = ready_task_ids(self._workflow, self.statuses)
        for task_id in ready:
            self.statuses[task_id] = transition(
                self.statuses[task_id], TaskStatus.READY, TransitionTrigger.DEPENDENCY_EVALUATION
            )
        return [task_id for task_id in self._order if self.statuses[task_id] is TaskStatus.READY]

    async def run_until_idle(self) -> dict[str, TaskStatus]:
        """Run every task that becomes ready without introducing random selection."""
        while True:
            self._begin_requested_retries()
            ready = self.recalculate_readiness()
            if self.actions.paused or not ready:
                return self.statuses.copy()
            await asyncio.gather(*(
                self._run_task(self._tasks[task_id])
                for task_id in ready
                if self.statuses[task_id] is TaskStatus.READY
            ))

    async def _run_task(self, task: TaskDefinition) -> None:
        self.statuses[task.id] = transition(
            TaskStatus.READY, TaskStatus.STARTING, TransitionTrigger.SCHEDULER
        )
        self._attempt_counts[task.id] += 1
        token = _task_context.set(task.id)
        try:
            result: ExecutionResult | ContinuationExecutionResult
            if task.execution_mode is ExecutionMode.CONTINUE_THREAD:
                result = await self._continuation.execute_task(
                    task,
                    {source_id: self._source(source_id) for source_id in self.thread_ids},
                    self._limiter,
                    self._workspace_locks,
                    self._thread_locks,
                )
            else:
                result = await self._executor.execute(task)
        except Exception:  # noqa: BLE001 - adapter and continuation failures must fail closed.
            self.statuses[task.id] = transition(
                TaskStatus.STARTING, TaskStatus.FAILED, TransitionTrigger.CODEX_EVENT
            )
            return
        finally:
            _task_context.reset(token)
        if not result.started:
            self.statuses[task.id] = transition(
                TaskStatus.STARTING, TaskStatus.FAILED, TransitionTrigger.CODEX_EVENT
            )
            return

        self.statuses[task.id] = transition(
            TaskStatus.STARTING, TaskStatus.RUNNING, TransitionTrigger.CODEX_EVENT
        )
        self.statuses[task.id] = transition(
            TaskStatus.RUNNING, result.status, TransitionTrigger.CODEX_EVENT
        )

    def _source(self, task_id: str) -> ContinuationSource:
        return ContinuationSource(
            task_id=task_id,
            status=self.statuses[task_id],
            thread_id=self.thread_ids.get(task_id),
            has_active_turn=self.statuses[task_id] in {TaskStatus.STARTING, TaskStatus.RUNNING},
        )

    def _request_retry(self, task_id: str) -> None:
        task = self._tasks[task_id]
        if self._attempt_counts[task_id] >= task.retry_policy.max_attempts:
            raise ManualActionError(f"retry limit reached for task: {task_id}")
        self._retry_requests.add(task_id)

    def _begin_requested_retries(self) -> None:
        for task_id in sorted(self._retry_requests):
            # A retry creates a fresh attempt. It starts at PENDING and then uses
            # the existing readiness and transition services for that attempt.
            self.statuses[task_id] = TaskStatus.PENDING
        self._retry_requests.clear()
