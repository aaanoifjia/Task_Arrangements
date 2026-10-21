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


def fork_join_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="root"),
            TaskDefinition(id="B", name="B", prompt="B", cwd="branch-b", dependencies=["A"]),
            TaskDefinition(id="C", name="C", prompt="C", cwd="branch-c", dependencies=["A"]),
            TaskDefinition(id="D", name="D", prompt="D", cwd="root", dependencies=["B", "C"]),
        ],
        edges=[
            Edge(source_task_id="A", target_task_id="B"),
            Edge(source_task_id="A", target_task_id="C"),
            Edge(source_task_id="B", target_task_id="D"),
            Edge(source_task_id="C", target_task_id="D"),
        ],
    )


class ForkJoinAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.prompt_by_turn: dict[str, str] = {}
        self.order: list[str] = []
        self.active = 0
        self.peak = 0

    async def start_turn(self, thread, prompt: str) -> CodexTurnRef:  # type: ignore[no-untyped-def]
        turn = await super().start_turn(thread, prompt)
        self.prompt_by_turn[turn.turn_id] = prompt
        self.order.append(f"start:{prompt}")
        return turn

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.active += 1
        self.peak = max(self.peak, self.active)
        prompt = self.prompt_by_turn[turn.turn_id]
        try:
            yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
            if prompt in {"B", "C"}:
                await asyncio.sleep(0.05)
            self.active -= 1
            self.order.append(f"complete:{prompt}")
            yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        finally:
            self.active = max(self.active, 0)


@pytest.mark.asyncio
async def test_persistent_fork_join_releases_join_only_after_both_branches(
    tmp_path: Path,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = ForkJoinAdapter()
    definition = fork_join_workflow()
    runner = DurableRunner(repository, adapter, max_concurrency=3)
    run_id = runner.prepare_run(definition)

    await runner.execute_run(run_id, definition)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    assert {row["status"] for row in rows.values()} == {"SUCCESS"}
    assert adapter.peak == 2
    d_start = adapter.order.index("start:D")
    assert d_start > adapter.order.index("complete:B")
    assert d_start > adapter.order.index("complete:C")
    assert repository.get_workflow_run(run_id)["status"] == "SUCCESS"
