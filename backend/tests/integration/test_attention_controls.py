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


def _setup(tmp_path: Path) -> tuple[StorageRepositories, RuntimeManager, str, str, str]:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    repository.save_workflow_definition(workflow())
    run_id = repository.create_workflow_run("workflow", {"workflow": "snapshot"})
    parent_id, child_id = repository.create_task_runs(run_id, ["A", "B"])
    repository.update_task_run_state(parent_id, "NEEDS_ATTENTION", "thread", "turn")
    repository.update_task_run_state(child_id, "BLOCKED")
    manager = RuntimeManager(repository, FakeCodexAdapter())
    manager._workflows[run_id] = workflow()
    return repository, manager, run_id, parent_id, child_id


@pytest.mark.asyncio
async def test_attention_cancel_is_explicit_and_does_not_release_child(tmp_path: Path) -> None:
    repository, manager, run_id, parent_id, child_id = _setup(tmp_path)

    result = await manager.cancel(run_id, parent_id)

    assert result.accepted is True
    assert repository.get_task_run(parent_id)["status"] == "CANCELLED"  # type: ignore[index]
    assert repository.get_task_run(child_id)["status"] == "BLOCKED"  # type: ignore[index]
    assert manager._adapter.calls == []


@pytest.mark.asyncio
async def test_attention_retry_is_explicit_and_does_not_assume_success(tmp_path: Path) -> None:
    repository, manager, run_id, parent_id, child_id = _setup(tmp_path)
    repository.create_attempt(parent_id, "NEEDS_ATTENTION")

    result = await manager.retry(run_id, parent_id)
    await manager.wait(run_id)

    assert result.accepted is True
    assert result.retry_requested is True
    assert repository.get_task_run(parent_id)["status"] == "SUCCESS"  # type: ignore[index]
    assert repository.get_task_run(child_id)["status"] == "SUCCESS"  # type: ignore[index]
    assert len(repository.load_attempts(parent_id)) == 2
    assert [row["event_type"] for row in repository.load_events_for_run(run_id)][-2:] == [
        "RETRY_REQUESTED",
        "MANUAL_ACTION_ACCEPTED",
    ]
