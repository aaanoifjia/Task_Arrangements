import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexThreadRef, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, ExecutionMode, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="."),
            TaskDefinition(
                id="B",
                name="B",
                prompt="B",
                cwd=".",
                dependencies=["A"],
                execution_mode=ExecutionMode.CONTINUE_THREAD,
                continue_from_task_id="A",
            ),
            TaskDefinition(
                id="C",
                name="C",
                prompt="C",
                cwd=".",
                dependencies=["A"],
                execution_mode=ExecutionMode.CONTINUE_THREAD,
                continue_from_task_id="A",
            ),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B"), Edge(source_task_id="A", target_task_id="C")],
    )


class SameThreadAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active_by_thread: dict[str, int] = {}
        self.peak_by_thread: dict[str, int] = {}

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef:
        self.calls.append("resume_thread")
        return thread

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        active = self.active_by_thread.get(turn.thread_id, 0) + 1
        self.active_by_thread[turn.thread_id] = active
        self.peak_by_thread[turn.thread_id] = max(self.peak_by_thread.get(turn.thread_id, 0), active)
        try:
            yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
            await asyncio.sleep(0.05)
            self.active_by_thread[turn.thread_id] -= 1
            yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        finally:
            self.active_by_thread[turn.thread_id] = max(self.active_by_thread[turn.thread_id], 0)


@pytest.mark.asyncio
async def test_durable_continuations_on_same_thread_are_serialized(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = SameThreadAdapter()
    definition = workflow()
    runner = DurableRunner(repository, adapter, max_concurrency=3)
    run_id = runner.prepare_run(definition)

    await runner.execute_run(run_id, definition)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    assert {row["status"] for row in rows.values()} == {"SUCCESS"}
    assert rows["A"]["thread_id"] == rows["B"]["thread_id"] == rows["C"]["thread_id"]
    assert adapter.peak_by_thread[rows["A"]["thread_id"]] == 1
    assert adapter.calls.count("create_thread") == 1
    assert adapter.calls.count("resume_thread") == 2
