import time
from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )


def seed_paused_run(database: Path, task_status: TaskStatus, thread_id: str | None = None) -> tuple[str, str]:
    connection = open_database(database)
    repository = StorageRepositories(connection)
    definition = workflow()
    repository.save_workflow_definition(definition)
    run_id = repository.create_workflow_run("workflow", definition.model_dump())
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
    repository.set_workflow_run_paused(run_id, True)
    repository.update_task_run_state(task_run_id, task_status.value, thread_id=thread_id)
    connection.close()
    return run_id, task_run_id


def test_paused_restart_reconciles_external_task_without_new_start(tmp_path: Path) -> None:
    database = tmp_path / "flow.sqlite3"
    run_id, task_run_id = seed_paused_run(database, TaskStatus.RUNNING, "thread-1")
    adapter = FakeCodexAdapter()

    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter=adapter)) as client:
        assert adapter.calls == ["read_thread"]
        assert client.get(f"/api/runs/{run_id}").status_code == 200
        assert "create_thread" not in adapter.calls

    connection = open_database(database)
    row = connection.execute("SELECT task_runs.status, workflow_runs.paused FROM task_runs JOIN workflow_runs ON workflow_runs.id = task_runs.workflow_run_id WHERE task_runs.id = ?", (task_run_id,)).fetchone()
    connection.close()
    assert row["status"] == TaskStatus.NEEDS_ATTENTION.value
    assert row["paused"] == 1


def test_paused_restart_releases_work_only_after_explicit_resume(tmp_path: Path) -> None:
    database = tmp_path / "flow.sqlite3"
    run_id, _ = seed_paused_run(database, TaskStatus.PENDING)
    adapter = FakeCodexAdapter()

    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter=adapter)) as client:
        assert adapter.calls == []
        response = client.post(f"/api/runs/{run_id}/resume")
        assert response.status_code == 200
        assert response.json()["action"] == "RESUME"
        for _ in range(20):
            if "create_thread" in adapter.calls:
                break
            time.sleep(0.01)
        assert "create_thread" in adapter.calls
