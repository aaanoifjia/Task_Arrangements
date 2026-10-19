from pathlib import Path

import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import Edge, TaskDefinition, WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
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


def _setup(tmp_path: Path) -> tuple[StorageRepositories, RuntimeManager, str, str, str]:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    parent_id, child_id = repository.create_task_runs(run_id, ["A", "B"])
    repository.update_task_run_state(parent_id, "READY")
    repository.update_task_run_state(child_id, "BLOCKED")
    return repository, RuntimeManager(repository, FakeCodexAdapter()), run_id, parent_id, child_id


@pytest.mark.asyncio
async def test_skip_does_not_release_dependent_child(tmp_path: Path) -> None:
    repository, manager, run_id, parent_id, child_id = _setup(tmp_path)

    result = await manager.skip(run_id, parent_id)
    assert result.accepted is True
    assert repository.get_task_run(parent_id)["status"] == "SKIPPED"  # type: ignore[index]

    await DurableRunner(repository, manager._adapter).execute_run(run_id, workflow())
    assert repository.get_task_run(child_id)["status"] == "BLOCKED"  # type: ignore[index]
    assert manager._adapter.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_status", ["PENDING", "RUNNING", "SUCCESS", "CANCELLED"])
async def test_skip_rejects_states_not_allowed_by_state_machine(
    tmp_path: Path, initial_status: str
) -> None:
    repository, manager, run_id, parent_id, _ = _setup(tmp_path)
    repository.update_task_run_state(parent_id, initial_status)

    result = await manager.skip(run_id, parent_id)

    assert result.accepted is False
    assert result.error_code == "TASK_NOT_SKIPPABLE"
    assert repository.get_task_run(parent_id)["status"] == initial_status  # type: ignore[index]
