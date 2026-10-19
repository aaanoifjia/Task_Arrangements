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
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


class CancelBeforeTerminalAdapter(FakeCodexAdapter):
    def __init__(self, repository: StorageRepositories, terminal: EventType) -> None:
        super().__init__()
        self._repository = repository
        self.task_run_id: str | None = None
        self.terminal = terminal
        self.cancelled = False

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        if self.task_run_id is not None and not self.cancelled:
            self.cancelled = True
            self._repository.update_task_run_state(self.task_run_id, "CANCELLED")
        yield CodexEvent(event_type=self.terminal, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal", [EventType.TURN_COMPLETED, EventType.TURN_FAILED])
async def test_cancel_wins_over_late_terminal_result(tmp_path: Path, terminal: EventType) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = CancelBeforeTerminalAdapter(repository, terminal)
    runner = DurableRunner(repository, adapter)
    run_id = runner.prepare_run(workflow())
    adapter.task_run_id = str(repository.load_task_runs(run_id)[0]["id"])

    await runner.execute_run(run_id, workflow())

    task_run = repository.get_task_run(adapter.task_run_id)
    assert task_run is not None and task_run["status"] == "CANCELLED"
    assert repository.get_workflow_run(run_id)["status"] == "FAILED"  # type: ignore[index]
    assert len(repository.load_attempts(adapter.task_run_id)) == 1
