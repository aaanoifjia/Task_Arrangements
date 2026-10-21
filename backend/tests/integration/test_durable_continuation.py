from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import Edge, ExecutionMode, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def continuation_workflow() -> WorkflowDefinition:
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


@pytest.mark.asyncio
async def test_durable_continuation_reuses_source_thread_and_starts_distinct_turn(
    tmp_path: Path,
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter()
    manager = RuntimeManager(repository, adapter)

    run_id = await manager.start(continuation_workflow())
    await manager.wait(run_id)

    rows = {str(row["task_id"]): row for row in repository.load_task_runs(run_id)}
    assert rows["A"]["status"] == "SUCCESS"
    assert rows["B"]["status"] == "SUCCESS"
    assert rows["A"]["thread_id"] == rows["B"]["thread_id"]
    assert rows["A"]["turn_id"] != rows["B"]["turn_id"]
    assert adapter.calls.count("create_thread") == 1
    assert adapter.calls.count("resume_thread") == 1
    assert adapter.calls.count("start_turn") == 2

