from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def test_authorized_diagnostics_returns_redacted_summary(tmp_path: Path) -> None:
    app = create_app(
        ServiceConfig.from_db_path(tmp_path / "diagnostics.sqlite3", token="diagnostic-token", desktop_mode=True),
        adapter=FakeCodexAdapter(),
    )

    with TestClient(app) as client:
        response = client.get("/api/system/diagnostics", headers={"Authorization": "Bearer diagnostic-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["db_schema_version"] == 3
    assert body["db_path_category"] == "configured"
    assert body["active_run_count"] == 0
    assert body["active_task_count"] == 0
    serialized = response.text.lower()
    assert "diagnostics.sqlite3" not in serialized
    assert "token" not in serialized
    assert "prompt" not in serialized


def test_unauthorized_desktop_diagnostics_fails_closed(tmp_path: Path) -> None:
    app = create_app(
        ServiceConfig.from_db_path(tmp_path / "diagnostics.sqlite3", token="diagnostic-token", desktop_mode=True),
        adapter=FakeCodexAdapter(),
    )

    with TestClient(app) as client:
        response = client.get("/api/system/diagnostics")

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "UNAUTHORIZED"
