"""Authenticated, redacted public runtime/about status."""

from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def test_status_exposes_safe_runtime_about_fields(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "status.sqlite3"), adapter=FakeCodexAdapter())

    with TestClient(app) as client:
        response = client.get("/api/system/status")

    assert response.status_code == 200
    body = response.json()
    assert body["app_version"] == "0.1.0"
    assert body["backend_version"] == "0.1.0"
    assert body["schema_version"] == 3
    assert body["desktop_mode"] is False
    assert body["runtime_available"] is True
    assert body["active_runtime_count"] == 0


def test_desktop_status_requires_auth_and_is_redacted(tmp_path: Path) -> None:
    app = create_app(
        ServiceConfig.from_db_path(tmp_path / "desktop-status.sqlite3", token="status-token", desktop_mode=True),
        adapter=FakeCodexAdapter(),
    )

    with TestClient(app) as client:
        unauthorized = client.get("/api/system/status")
        authorized = client.get("/api/system/status", headers={"Authorization": "Bearer status-token"})

    assert unauthorized.status_code == 401
    assert unauthorized.json()["detail"]["error"]["code"] == "UNAUTHORIZED"
    assert authorized.status_code == 200
    body = authorized.json()
    assert body["desktop_mode"] is True
    serialized = authorized.text.lower()
    assert "status-token" not in serialized
    assert "credential" not in serialized
    assert "codex_home" not in serialized
    assert "sqlite3" not in serialized
