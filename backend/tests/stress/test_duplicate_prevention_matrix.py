from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexEvent, CodexTurnRef, EventType
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories

MATRIX = (
    ("success", EventType.TURN_COMPLETED, "SUCCESS", "SUCCESS"),
    ("tool_failure", EventType.TURN_COMPLETED, "FAILED", "BLOCKED"),
    ("interrupt", EventType.TURN_INTERRUPTED, "INTERRUPTED", "BLOCKED"),
    ("turn_failure", EventType.TURN_FAILED, "FAILED", "BLOCKED"),
    ("attention", EventType.ATTENTION_REQUIRED, "NEEDS_ATTENTION", "BLOCKED"),
    ("stream_crash", None, "FAILED", "BLOCKED"),
)


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="duplicate-prevention",
        name="Duplicate Prevention",
        tasks=[
            TaskDefinition(id="A", name="A", prompt="parent", cwd="."),
            TaskDefinition(id="B", name="B", prompt="child", cwd=".", dependencies=["A"]),
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


class MatrixAdapter(FakeCodexAdapter):
    def __init__(self, mode: str, terminal: EventType | None = None) -> None:
        super().__init__()
        self.mode = mode
        self.terminal = terminal
        self.prompts: list[str] = []
        self.turns: list[str] = []

    async def start_turn(self, thread, prompt: str) -> CodexTurnRef:  # type: ignore[no-untyped-def]
        turn = await super().start_turn(thread, prompt)
        self.prompts.append(prompt)
        self.turns.append(turn.turn_id)
        return turn

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        if self.mode == "tool_failure" or (self.mode == "retry" and len(self.prompts) == 1):
            yield CodexEvent(
                event_type=EventType.TOOL_COMPLETED,
                thread_id=turn.thread_id,
                turn_id=turn.turn_id,
                details={"item_type": "command_execution", "status": "failed", "exit_code": 1},
            )
        if self.mode == "stream_crash":
            return
        if self.terminal is None:
            yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        else:
            yield CodexEvent(event_type=self.terminal, thread_id=turn.thread_id, turn_id=turn.turn_id)


def assert_one_prompt_per_attempt(repository: StorageRepositories, adapter: MatrixAdapter, run_id: str) -> None:
    attempts = [attempt for row in repository.load_task_runs(run_id) for attempt in repository.load_attempts(str(row["id"]))]
    assert len(adapter.prompts) == len(attempts)
    assert len(adapter.turns) == len(set(adapter.turns))


@pytest.mark.asyncio
@pytest.mark.parametrize("mode,terminal,parent_status,child_status", MATRIX)
async def test_deterministic_event_matrix_prevents_duplicate_prompts_and_release(
    tmp_path: Path,
    mode: str,
    terminal: EventType | None,
    parent_status: str,
    child_status: str,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / f"{mode}.sqlite3"))
    adapter = MatrixAdapter(mode, terminal)
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    assert rows["A"]["status"] == parent_status
    assert rows["B"]["status"] == child_status
    assert_one_prompt_per_attempt(repository, adapter, run_id)


@pytest.mark.asyncio
async def test_manual_retry_matrix_reuses_no_attempt_prompt_and_releases_only_after_success(
    tmp_path: Path,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "retry.sqlite3"))
    adapter = MatrixAdapter("retry", EventType.TURN_COMPLETED)
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(workflow())
    await manager.wait(run_id)
    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    parent_id = str(rows["A"]["id"])
    assert rows["A"]["status"] == "FAILED"
    assert rows["B"]["status"] == "BLOCKED"
    assert_one_prompt_per_attempt(repository, adapter, run_id)

    result = await manager.retry(run_id, parent_id)
    assert result.accepted is True
    await manager.wait(run_id)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    assert rows["A"]["status"] == "SUCCESS"
    assert rows["B"]["status"] == "SUCCESS"
    assert_one_prompt_per_attempt(repository, adapter, run_id)
    assert len(repository.load_attempts(parent_id)) == 2
