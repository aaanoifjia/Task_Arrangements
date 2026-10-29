from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/api/workflows",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )


def test_configured_tauri_origin_is_allowed_with_credentials(tmp_path: Path) -> None:
    config = ServiceConfig.from_db_path(
        tmp_path / "desktop.sqlite3",
        desktop_mode=True,
        cors_origins=("http://tauri.localhost",),
    )

    with TestClient(create_app(config)) as client:
        response = _preflight(client, "http://tauri.localhost")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://tauri.localhost"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_authenticated_api_request_still_requires_bearer_token(tmp_path: Path) -> None:
    config = ServiceConfig.from_db_path(
        tmp_path / "desktop.sqlite3",
        desktop_mode=True,
        token="desktop-token",
        cors_origins=("http://tauri.localhost",),
    )

    with TestClient(create_app(config)) as client:
        unauthorized = client.get("/api/workflows", headers={"Origin": "http://tauri.localhost"})
        authorized = client.get(
            "/api/workflows",
            headers={"Origin": "http://tauri.localhost", "Authorization": "Bearer desktop-token"},
        )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_unconfigured_origin_is_rejected_and_wildcard_is_not_used(tmp_path: Path) -> None:
    config = ServiceConfig.from_db_path(
        tmp_path / "desktop.sqlite3",
        desktop_mode=True,
        cors_origins=("http://tauri.localhost",),
    )

    with TestClient(create_app(config)) as client:
        response = _preflight(client, "http://evil.example")

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    assert "*" not in response.headers.get("access-control-allow-origin", "")
