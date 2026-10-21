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
        ],
        edges=[Edge(source_task_id="A", target_task_id="B")],
    )


class ObservingContinuationAdapter(FakeCodexAdapter):
    def __init__(self, database_path: Path, target_task_run_id: str) -> None:
        super().__init__()
        self.database_path = database_path
        self.target_task_run_id = target_task_run_id
        self.observed_pre_external_commit = False

    async def resume_thread(self, thread: CodexThreadRef) -> CodexThreadRef:
        connection = open_database(self.database_path)
        row = connection.execute(
            "SELECT status FROM task_runs WHERE id = ?", (self.target_task_run_id,)
        ).fetchone()
        attempts = connection.execute(
            "SELECT count(*) FROM attempts WHERE task_run_id = ?", (self.target_task_run_id,)
        ).fetchone()[0]
        connection.close()
        self.observed_pre_external_commit = row["status"] == "STARTING" and attempts == 1
        return await super().resume_thread(thread)

    async def stream_turn(self, turn: CodexTurnRef) -> AsyncIterator[CodexEvent]:
        self.calls.append("stream_turn")
        yield CodexEvent(event_type=EventType.TURN_STARTED, thread_id=turn.thread_id, turn_id=turn.turn_id)
        yield CodexEvent(event_type=EventType.TURN_COMPLETED, thread_id=turn.thread_id, turn_id=turn.turn_id)


@pytest.mark.asyncio
async def test_continuation_attempt_is_committed_before_resume_and_refs_are_recorded(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "flow.sqlite3"
    repository = StorageRepositories(open_database(database_path))
    definition = workflow()
    repository.save_workflow_definition(definition)
    run_id = repository.create_workflow_run(definition.id, {})
    repository.create_task_runs(run_id, ["A", "B"])
    repository.update_workflow_run_state(run_id, "RUNNING")
    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    adapter = ObservingContinuationAdapter(database_path, str(rows["B"]["id"]))
    await DurableRunner(repository, adapter).execute_run(run_id, definition)

    observed_rows = {
        str(row["task_id"]): row for row in repository.load_task_runs(run_id)
    }
    assert adapter.observed_pre_external_commit is True
    assert observed_rows["A"]["thread_id"] == observed_rows["B"]["thread_id"]
    assert observed_rows["A"]["turn_id"] != observed_rows["B"]["turn_id"]
