from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig


def payload() -> dict[str, object]:
    return {
        "id": "workflow-export-api",
        "name": "Export API workflow",
        "tasks": [{"id": "A", "name": "A", "prompt": "Illustrative", "cwd": "."}],
        "edges": [],
    }


def test_workflow_export_returns_stable_definition_envelope(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        assert client.post("/api/workflows", json=payload()).status_code == 201
        response = client.get("/api/workflows/workflow-export-api/export")

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "codex_flow.workflow_definition"
    assert body["schema_version"] == 1
    assert body["workflow"]["id"] == "workflow-export-api"
    assert "events" not in body
    assert "sdk" not in response.text.lower()


def test_workflow_export_returns_stable_not_found(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        response = client.get("/api/workflows/missing/export")

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "WORKFLOW_NOT_FOUND"
