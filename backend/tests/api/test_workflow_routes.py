from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig


def payload(name: str = "Workflow") -> dict[str, object]:
    return {
        "id": "workflow",
        "name": name,
        "tasks": [{"id": "A", "name": "A", "prompt": "A", "cwd": "."}],
        "edges": [],
    }


def test_workflow_create_get_update_list_and_stable_404(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        created = client.post("/api/workflows", json=payload())
        assert created.status_code == 201
        assert created.json()["workflow"]["name"] == "Workflow"
        assert client.get("/api/workflows/workflow").status_code == 200
        assert client.get("/api/workflows").json()[0]["id"] == "workflow"

        updated = client.put("/api/workflows/workflow", json=payload("Edited"))
        assert updated.status_code == 200
        assert updated.json()["workflow"]["name"] == "Edited"

        missing = client.get("/api/workflows/missing")
        assert missing.status_code == 404
        assert missing.json()["detail"]["error"]["code"] == "WORKFLOW_NOT_FOUND"


def test_workflow_update_requires_matching_ids(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        response = client.put("/api/workflows/other", json=payload())

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "WORKFLOW_ID_MISMATCH"
