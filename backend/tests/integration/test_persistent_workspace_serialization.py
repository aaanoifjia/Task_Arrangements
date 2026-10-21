import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    shared = "shared-branch"
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="root"),
            TaskDefinition(id="B", name="B", prompt="B", cwd=shared, dependencies=["A"]),
            TaskDefinition(id="C", name="C", prompt="C", cwd=shared, dependencies=["A"]),
            TaskDefinition(id="D", name="D", prompt="D", cwd="root", dependencies=["B", "C"]),
        ],
        edges=[
            Edge(source_task_id="A", target_task_id="B"),
            Edge(source_task_id="A", target_task_id="C"),
            Edge(source_task_id="B", target_task_id="D"),
            Edge(source_task_id="C", target_task_id="D"),
        ],
    )


class WorkspaceAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.prompt_by_turn: dict[str, str] = {}
        self.order: list[str] = []
        self.active_branch = 0
        self.peak_branch = 0

    async def start_turn(self, thread, prompt: str) -> CodexTurnRef:  # type: ignore[no-untyped-def]
        turn = await super().start_turn(thread, prompt)
        self.prompt_by_turn[turn.turn_id] = prompt
        self.order.append(f"start:{prompt}")
        return turn

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        prompt = self.prompt_by_turn[turn.turn_id]
        is_branch = prompt in {"B", "C"}
        if is_branch:
            self.active_branch += 1
            self.peak_branch = max(self.peak_branch, self.active_branch)
        try:
            yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
            if is_branch:
                await asyncio.sleep(0.05)
            if is_branch:
                self.active_branch -= 1
            self.order.append(f"complete:{prompt}")
            yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        finally:
            self.active_branch = max(self.active_branch, 0)


@pytest.mark.asyncio
async def test_same_workspace_fork_branches_serialize_before_join(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = WorkspaceAdapter()
    definition = workflow()
    runner = DurableRunner(repository, adapter, max_concurrency=3)
    run_id = runner.prepare_run(definition)

    await runner.execute_run(run_id, definition)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    assert {row["status"] for row in rows.values()} == {"SUCCESS"}
    assert adapter.peak_branch == 1
    d_start = adapter.order.index("start:D")
    assert d_start > adapter.order.index("complete:B")
    assert d_start > adapter.order.index("complete:C")
