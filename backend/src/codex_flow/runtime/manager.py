"""Tracked non-blocking execution of durable workflow runs."""

import asyncio

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.domain.models import WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.repositories import StorageRepositories


class RuntimeManager:
    def __init__(self, repository: StorageRepositories, adapter: CodexAdapter) -> None:
        self._repository = repository
        self._adapter = adapter
        self._runner = DurableRunner(repository, adapter)
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._accepting = True

    async def start(self, workflow: WorkflowDefinition) -> str:
        if not self._accepting:
            raise RuntimeError("runtime manager is shutting down")
        run_id = self._runner.prepare_run(workflow)
        task = asyncio.create_task(self._runner.execute_run(run_id, workflow))
        self._tasks[run_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(run_id, None))
        return run_id

    async def wait(self, run_id: str) -> None:
        task = self._tasks.get(run_id)
        if task is None:
            row = self._repository.get_workflow_run(run_id)
            if row is None:
                raise KeyError(f"run not found: {run_id}")
            return
        await task

    @property
    def active_count(self) -> int:
        return len(self._tasks)

    async def shutdown(self) -> None:
        self._accepting = False
        tasks = tuple(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
