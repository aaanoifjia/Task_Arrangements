import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexThreadRef, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories

ITERATIONS = 24


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="accelerated-soak",
        name="Accelerated soak",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="parent", cwd="."),
            TaskDefinition(id="B", name="B", prompt="child", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


class SoakAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.parent_count = 0
        self.prompts: list[str] = []
        self.turn_modes: dict[str, bool] = {}

    async def start_turn(self, thread: CodexThreadRef, prompt: str) -> CodexTurnRef:
        turn = await super().start_turn(thread, prompt)
        self.prompts.append(prompt)
        if prompt == "parent":
            self.parent_count += 1
            self.turn_modes[turn.turn_id] = self.parent_count % 4 == 0
        else:
            self.turn_modes[turn.turn_id] = False
        return turn

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        if self.turn_modes[turn.turn_id]:
            yield CodexEvent(
                event_type=EventType.TOOL_COMPLETED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
                details={"item_type": "command_execution", "status": "failed", "exit_code": 1},
            )
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_accelerated_fake_workflow_soak_has_no_task_or_db_leaks(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "soak.sqlite3"))
    adapter = SoakAdapter()
    manager = RuntimeManager(repository, adapter)
    workflow_definition = workflow()
    baseline_tasks = {id(task) for task in asyncio.all_tasks() if not task.done()}
    run_ids: list[str] = []

    for _ in range(ITERATIONS):
        run_id = await manager.start(workflow_definition)
        run_ids.append(run_id)
        await manager.wait(run_id)

    failed_runs = 0
    for run_id in run_ids:
        rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
        parent_failed = rows["A"]["status"] == "FAILED"
        failed_runs += int(parent_failed)
        assert rows["B"]["status"] == ("BLOCKED" if parent_failed else "SUCCESS")
        assert len(repository.load_attempts(str(rows["A"]["id"]))) == 1
        assert len(repository.load_attempts(str(rows["B"]["id"]))) == (0 if parent_failed else 1)
        task_ids = [str(rows[task_id]["id"]) for task_id in ("A", "B")]
        placeholders = ", ".join("?" for _ in task_ids)
        event_count = repository._connection.execute(
            f"SELECT count(*) FROM events WHERE task_run_id IN ({placeholders})", task_ids
        ).fetchone()[0]
        assert event_count >= 2

    expected_prompts = (ITERATIONS - failed_runs) * 2 + failed_runs
    assert len(adapter.prompts) == expected_prompts
    assert len(adapter.turn_modes) == expected_prompts
    assert repository.load_active_runs() == []
    assert manager.active_count == 0
    await asyncio.sleep(0)
    assert {id(task) for task in asyncio.all_tasks() if not task.done()} == baseline_tasks
