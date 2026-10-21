"""REST token protection tests for desktop mode."""

from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api.app import create_app
from codex_flow.api.config import ServiceConfig


def test_health_handshake_is_token_safe(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "token.sqlite3", token="secret"))

    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_configured_token_rejects_missing_and_wrong_rest_credentials(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "token.sqlite3", token="secret"))

    with TestClient(app) as client:
        missing = client.get("/api/workflows")
        wrong = client.get("/api/workflows", headers={"Authorization": "Bearer wrong"})

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert "secret" not in missing.text
    assert "secret" not in wrong.text


def test_configured_token_allows_authorized_rest_request(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "token.sqlite3", token="secret"))

    with TestClient(app) as client:
        response = client.get("/api/workflows", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
