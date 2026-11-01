from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_status", ["PENDING", "BLOCKED", "READY"])
async def test_cancel_queued_task_does_not_execute_external_work(
    tmp_path: Path, initial_status: str
) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter()
    manager = RuntimeManager(repository, adapter)
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    if initial_status != "PENDING":
        repository.update_task_run_state(task_run_id, initial_status)

    result = await manager.cancel(run_id, task_run_id)

    assert result.accepted is True
    assert result.status.value == "CANCELLED"
    assert repository.get_task_run(task_run_id)["status"] == "CANCELLED"  # type: ignore[index]
    assert adapter.calls == []
    assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_ACCEPTED"


@pytest.mark.asyncio
async def test_cancel_last_task_finalizes_run_without_external_work(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter()
    manager = RuntimeManager(repository, adapter)
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_workflow_run_state(run_id, "RUNNING")
    repository.update_task_run_state(task_run_id, "READY")

    result = await manager.cancel(run_id, task_run_id)

    assert result.accepted is True
    assert repository.get_workflow_run(run_id)["status"] == "FAILED"  # type: ignore[index]
    assert adapter.calls == []
