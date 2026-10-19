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
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="A", cwd="."),
            TaskDefinition(id="B", name="B", prompt="B", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


class PauseAfterStartAdapter(FakeCodexAdapter):
    def __init__(self, repository: StorageRepositories) -> None:
        super().__init__()
        self._repository = repository
        self.run_id: str | None = None
        self._paused_once = False

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        async for event in super().stream_turn(turn):
            yield event
            if (
                event.event_type is EventType.TURN_STARTED
                and self.run_id is not None
                and not self._paused_once
            ):
                self._paused_once = True
                self._repository.set_workflow_run_paused(self.run_id, True)


@pytest.mark.asyncio
async def test_pause_between_tasks_prevents_new_external_start_but_allows_current_finish(
    tmp_path: Path,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = PauseAfterStartAdapter(repository)
    runner = DurableRunner(repository, adapter)
    run_id = runner.prepare_run(workflow())
    adapter.run_id = run_id

    await runner.execute_run(run_id, workflow())

    rows = {row["task_id"]: row for row in repository.load_task_runs(run_id)}
    assert rows["A"]["status"] == "SUCCESS"
    assert rows["B"]["status"] == "BLOCKED"
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"]
    assert repository.get_workflow_run_paused(run_id) is True

    repository.set_workflow_run_paused(run_id, False)
    await runner.execute_run(run_id, workflow())

    assert {row["task_id"]: row["status"] for row in repository.load_task_runs(run_id)} == {
        "A": "SUCCESS",
        "B": "SUCCESS",
    }
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"] * 2
