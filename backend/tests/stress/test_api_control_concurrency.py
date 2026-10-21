import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import TaskDefinition, WorkflowDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def seed_run(database: Path) -> tuple[str, str]:
    repository = StorageRepositories(open_database(database))
    workflow = WorkflowDefinition(
        id="workflow",
        name="Workflow",
        tasks=[TaskDefinition(id="A", name="A", prompt="A", cwd=".")],
        edges=[],
    )
    repository.save_workflow_definition(workflow)
    run_id = repository.create_workflow_run(workflow.id, workflow.model_dump())
    task_run_id = repository.create_task_runs(run_id, ["A"])[0]
    repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
    repository.update_task_run_state(task_run_id, TaskStatus.READY.value)
    repository._connection.close()
    return run_id, task_run_id


def test_concurrent_api_reads_and_controls_leave_consistent_state(tmp_path: Path) -> None:
    database = tmp_path / "api.sqlite3"
    run_id, _ = seed_run(database)
    app = create_app(ServiceConfig.from_db_path(database), adapter=FakeCodexAdapter())
    paths = [
        ("GET", f"/api/runs/{run_id}"),
        ("GET", f"/api/runs/{run_id}/tasks"),
        ("POST", f"/api/runs/{run_id}/pause"),
        ("POST", f"/api/runs/{run_id}/resume"),
        ("POST", f"/api/runs/{run_id}/tasks/A/cancel"),
        ("POST", f"/api/runs/{run_id}/tasks/A/skip"),
        ("POST", f"/api/runs/{run_id}/tasks/A/mark-success"),
        ("POST", f"/api/runs/{run_id}/tasks/A/retry"),
    ] * 12

    with TestClient(app) as client:
        def request(path: tuple[str, str]) -> int:
            method, url = path
            response = client.get(url) if method == "GET" else client.post(url)
            return response.status_code

        with ThreadPoolExecutor(max_workers=16) as executor:
            statuses = list(executor.map(request, paths))

    assert all(status in {200, 404, 409, 422} for status in statuses)
    connection = open_database(database)
    run = connection.execute("SELECT status FROM workflow_runs WHERE id = ?", (run_id,)).fetchone()
    task = connection.execute("SELECT status FROM task_runs WHERE workflow_run_id = ?", (run_id,)).fetchone()
    events = connection.execute(
        "SELECT event_type, payload_json FROM events WHERE workflow_run_id = ? ORDER BY rowid",
        (run_id,),
    ).fetchall()
    assert run["status"] in {status.value for status in TaskStatus}
    assert task["status"] in {status.value for status in TaskStatus}
    assert all(isinstance(json.loads(str(event["payload_json"])), dict) for event in events)
    assert any(status == 409 for status in statuses)
