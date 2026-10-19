from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.api.lifespan import get_repositories
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.runtime.manager import RuntimeManager


def workflow_payload() -> dict[str, object]:
    return {
        "id": "workflow",
        "name": "Workflow",
        "tasks": [{"id": "A", "name": "A", "prompt": "A", "cwd": "."}],
        "edges": [],
    }


def test_run_start_and_history_endpoints(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        app.state.runtime = RuntimeManager(get_repositories(app), FakeCodexAdapter())
        assert client.post("/api/workflows", json=workflow_payload()).status_code == 201
        started = client.post("/api/workflows/workflow/runs")
        assert started.status_code == 202
        run_id = started.json()["run_id"]

        assert client.get("/api/runs").json()[0]["id"] == run_id
        assert client.get(f"/api/runs/{run_id}").json()["status"] == "SUCCESS"
        task = client.get(f"/api/runs/{run_id}/tasks/A")
        assert task.status_code == 200
        assert task.json()["status"] == "SUCCESS"
        assert len(client.get(f"/api/runs/{run_id}/tasks/A/attempts").json()) == 1


def test_run_routes_return_stable_missing_and_runtime_errors(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        assert client.post("/api/workflows/missing/runs").json()["detail"]["error"]["code"] == "RUNTIME_UNAVAILABLE"
        app.state.runtime = RuntimeManager(get_repositories(app), FakeCodexAdapter())
        response = client.post("/api/workflows/missing/runs")

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "WORKFLOW_NOT_FOUND"
