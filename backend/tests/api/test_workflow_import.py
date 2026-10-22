import json
from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig


def payload(workflow_id: str = "workflow-import-api") -> dict[str, object]:
    return {
        "kind": "codex_flow.workflow_definition",
        "schema_version": 1,
        "workflow": {
            "id": workflow_id,
            "name": "Import API workflow",
            "description": None,
            "tasks": [{"id": "A", "name": "A", "prompt": "Illustrative", "cwd": "."}],
            "edges": [],
        },
    }


def test_workflow_import_persists_one_definition(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        response = client.post("/api/workflows/import", json=payload())
        listing = client.get("/api/workflows")

    assert response.status_code == 201
    assert response.json()["workflow"]["id"] == "workflow-import-api"
    assert [item["id"] for item in listing.json()] == ["workflow-import-api"]


def test_workflow_import_returns_stable_conflict_and_explicit_replacement(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with TestClient(app) as client:
        assert client.post("/api/workflows", json=payload()["workflow"]).status_code == 201
        conflict = client.post("/api/workflows/import", json=payload())
        replacement_body = {**payload(), "replacement_id": "workflow-import-copy"}
        replaced = client.post("/api/workflows/import", json=replacement_body)

    assert conflict.status_code == 409
    assert conflict.json()["detail"]["error"]["code"] == "WORKFLOW_IMPORT_CONFLICT"
    assert replaced.status_code == 201
    assert replaced.json()["workflow"]["id"] == "workflow-import-copy"


def test_workflow_import_returns_stable_errors_for_malformed_data(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))
    cyclic = payload()
    workflow = cyclic["workflow"]
    assert isinstance(workflow, dict)
    workflow["tasks"] = [
        {"id": "A", "name": "A", "prompt": "Illustrative", "cwd": ".", "dependencies": ["B"]},
        {"id": "B", "name": "B", "prompt": "Illustrative", "cwd": ".", "dependencies": ["A"]},
    ]
    workflow["edges"] = [
        {"source_task_id": "A", "target_task_id": "B"},
        {"source_task_id": "B", "target_task_id": "A"},
    ]

    with TestClient(app) as client:
        malformed = client.post("/api/workflows/import", content="not-json", headers={"content-type": "application/json"})
        invalid = client.post("/api/workflows/import", json={"kind": "wrong", "schema_version": 1, "workflow": {}})
        cycle = client.post("/api/workflows/import", content=json.dumps(cyclic), headers={"content-type": "application/json"})

    assert malformed.status_code == 400
    assert malformed.json()["detail"]["error"]["code"] == "INVALID_WORKFLOW_IMPORT"
    assert invalid.status_code == 400
    assert invalid.json()["detail"]["error"]["code"] == "INVALID_WORKFLOW_IMPORT"
    assert cycle.status_code == 400
    assert cycle.json()["detail"]["error"]["code"] == "INVALID_WORKFLOW_IMPORT"
