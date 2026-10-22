"""Stable cursor pagination for run history."""

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


def test_run_history_pages_have_no_duplicates_or_gaps(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "pagination.sqlite3"))
    with TestClient(app) as client:
        app.state.runtime = RuntimeManager(get_repositories(app), FakeCodexAdapter())
        assert client.post("/api/workflows", json=workflow_payload()).status_code == 201
        created = [client.post("/api/workflows/workflow/runs").json()["run_id"] for _ in range(5)]

        first = client.get("/api/runs", params={"limit": 2})
        assert first.status_code == 200
        first_page = first.json()
        assert len(first_page["items"]) == 2
        assert first_page["next_cursor"]

        second = client.get("/api/runs", params={"limit": 2, "cursor": first_page["next_cursor"]})
        assert second.status_code == 200
        second_page = second.json()
        assert len(second_page["items"]) == 2

        third = client.get("/api/runs", params={"limit": 2, "cursor": second_page["next_cursor"]})
        assert third.status_code == 200
        third_page = third.json()
        assert len(third_page["items"]) == 1
        assert third_page["next_cursor"] is None

        paged_ids = [item["id"] for page in (first_page, second_page, third_page) for item in page["items"]]
        expected = [item["id"] for item in client.get("/api/runs").json()]
        assert paged_ids == expected
        assert set(paged_ids) == set(created)


def test_default_run_history_response_remains_a_list(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "compatibility.sqlite3"))
    with TestClient(app) as client:
        app.state.runtime = RuntimeManager(get_repositories(app), FakeCodexAdapter())
        assert client.post("/api/workflows", json=workflow_payload()).status_code == 201
        run_id = client.post("/api/workflows/workflow/runs").json()["run_id"]

        response = client.get("/api/runs")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["id"] == run_id


def test_invalid_run_cursor_is_explicit(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "invalid-cursor.sqlite3"))
    with TestClient(app) as client:
        app.state.runtime = RuntimeManager(get_repositories(app), FakeCodexAdapter())

        response = client.get("/api/runs", params={"cursor": "not-a-cursor"})

        assert response.status_code == 400
        assert response.json()["detail"]["error"]["code"] == "INVALID_RUN_CURSOR"
