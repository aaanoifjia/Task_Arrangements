from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
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


@pytest.mark.asyncio
async def test_mark_success_releases_valid_children_and_is_auditable(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    adapter = FakeCodexAdapter()
    manager = RuntimeManager(repository, adapter)
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    parent_id, child_id = repository.create_task_runs(run_id, ["A", "B"])
    repository.update_task_run_state(parent_id, "READY")
    repository.update_task_run_state(child_id, "PENDING")
    manager._workflows[run_id] = workflow()

    result = await manager.mark_success(run_id, parent_id)
    await manager.wait(run_id)

    assert result.accepted is True
    assert repository.get_task_run(parent_id)["status"] == "SUCCESS"  # type: ignore[index]
    assert repository.get_task_run(child_id)["status"] == "SUCCESS"  # type: ignore[index]
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"]
    assert repository.load_events_for_run(run_id)[-1]["event_type"] == "MANUAL_ACTION_ACCEPTED"


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_status", ["PENDING", "BLOCKED", "SUCCESS", "FAILED"])
async def test_mark_success_rejects_non_ready_states(tmp_path: Path, initial_status: str) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter())
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    parent_id, _ = repository.create_task_runs(run_id, ["A", "B"])
    repository.update_task_run_state(parent_id, initial_status)

    result = await manager.mark_success(run_id, parent_id)

    assert result.accepted is False
    assert result.error_code == "TASK_NOT_MARKABLE"
