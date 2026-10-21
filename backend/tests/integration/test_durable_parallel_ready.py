import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="workspace-a"),
            TaskDefinition(id="B", name="B", prompt="B", cwd="workspace-b"),
        ],
        edges=[],
    )


class DelayedAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.active = 0
        self.peak = 0
        self.started_prompts: list[str] = []

    async def start_turn(self, thread, prompt: str) -> CodexTurnRef:  # type: ignore[no-untyped-def]
        self.started_prompts.append(prompt)
        return await super().start_turn(thread, prompt)

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        self.active += 1
        self.peak = max(self.peak, self.active)
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        await asyncio.sleep(0.05)
        self.active -= 1
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(("limit", "expected_peak"), [(1, 1), (2, 2)])
async def test_independent_ready_tasks_overlap_only_up_to_global_limit(
    tmp_path: Path, limit: int, expected_peak: int
) -> None:
    repository = StorageRepositories(open_database(tmp_path / f"flow-{limit}.sqlite3"))
    adapter = DelayedAdapter()
    definition = workflow()
    runner = DurableRunner(repository, adapter, max_concurrency=limit)
    run_id = runner.prepare_run(definition)

    await runner.execute_run(run_id, definition)

    assert adapter.peak == expected_peak
    assert adapter.started_prompts == ["A", "B"]
    assert {row["status"] for row in repository.load_task_runs(run_id)} == {"SUCCESS"}


def test_durable_runner_rejects_non_positive_capacity(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))

    with pytest.raises(ValueError, match="max_concurrency must be positive"):
        DurableRunner(repository, FakeCodexAdapter(), max_concurrency=0)
