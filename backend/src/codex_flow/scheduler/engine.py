"""Deterministic asynchronous scheduler for a workflow definition."""

import asyncio
from collections.abc import Mapping

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.executor import TaskExecutor
from codex_flow.scheduler.graph import dependency_map, topological_order
from codex_flow.scheduler.locks import (
    GlobalConcurrencyLimiter,
    ThreadTurnLockManager,
    WorkspaceLockManager,
)
from codex_flow.scheduler.readiness import ready_task_ids
from codex_flow.scheduler.state_machine import TransitionTrigger, transition


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
        self._executor = TaskExecutor(
            adapter,
            GlobalConcurrencyLimiter(max_concurrency),
            WorkspaceLockManager(),
            ThreadTurnLockManager(),
        )

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
        while ready := self.recalculate_readiness():
            await asyncio.gather(*(
                self._run_task(self._tasks[task_id])
                for task_id in ready
                if self.statuses[task_id] is TaskStatus.READY
            ))
        return self.statuses.copy()

    async def _run_task(self, task: TaskDefinition) -> None:
        self.statuses[task.id] = transition(
            TaskStatus.READY, TaskStatus.STARTING, TransitionTrigger.SCHEDULER
        )
        result = await self._executor.execute(task)
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
