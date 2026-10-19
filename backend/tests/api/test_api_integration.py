from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter, FakeScenario


def workflow_payload(*, fork: bool = False) -> dict[str, object]:
    tasks: list[dict[str, object]] = [
        {"id": "A", "name": "A", "prompt": "A", "cwd": "."},
        {"id": "B", "name": "B", "prompt": "B", "cwd": ".", "dependencies": ["A"]},
    ]
    return {
        "id": "workflow",
        "name": "Workflow",
        "tasks": tasks,
        "edges": [{"source_task_id": "A", "target_task_id": "B"}],
    }


def test_successful_workflow_api_and_restart_persist_history(tmp_path: Path) -> None:
    database = tmp_path / "integration.sqlite3"
    first_adapter = FakeCodexAdapter()
    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter=first_adapter)) as client:
        assert client.post("/api/workflows", json=workflow_payload()).status_code == 201
        assert client.get("/api/workflows/workflow").status_code == 200
        started = client.post("/api/workflows/workflow/runs")
        assert started.status_code == 202
        run_id = started.json()["run_id"]
        status = "PENDING"
        for _ in range(10):
            status = client.get(f"/api/runs/{run_id}").json()["status"]
            if status == "SUCCESS":
                break
        assert status == "SUCCESS"
        tasks = client.get(f"/api/runs/{run_id}/tasks").json()
        assert [task["status"] for task in tasks] == ["SUCCESS", "SUCCESS"]
        assert len(client.get(f"/api/runs/{run_id}/tasks/A/attempts").json()) == 1
    second_adapter = FakeCodexAdapter()
    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter=second_adapter)) as client:
        assert client.get("/api/workflows/workflow").status_code == 200
        assert client.get(f"/api/runs/{run_id}").json()["status"] == "SUCCESS"
        assert len(client.get(f"/api/runs/{run_id}/tasks/A/attempts").json()) == 1


def test_failed_parent_is_exposed_and_child_remains_blocked(tmp_path: Path) -> None:
    database = tmp_path / "failure.sqlite3"
    adapter = FakeCodexAdapter(FakeScenario.FAILED)
    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter=adapter)) as client:
        assert client.post("/api/workflows", json=workflow_payload()).status_code == 201
        run_id = client.post("/api/workflows/workflow/runs").json()["run_id"]
        tasks = client.get(f"/api/runs/{run_id}/tasks").json()
        statuses = {task["task_id"]: task["status"] for task in tasks}
        assert statuses == {"A": "FAILED", "B": "BLOCKED"}
        assert adapter.calls.count("create_thread") == 1
