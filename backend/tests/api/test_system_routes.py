from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def test_health_and_system_status_are_local_and_secret_free(tmp_path: Path) -> None:
    adapter = FakeCodexAdapter()
    app = create_app(ServiceConfig.from_db_path(tmp_path / "system.sqlite3"), adapter=adapter)

    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        response = client.get("/api/system/status")
        assert response.status_code == 200
        body = response.json()
        assert body == {
            "service": "ok",
            "database": "reachable",
                "schema_version": 3,
            "active_runtime_count": 0,
        }
        serialized = response.text.lower()
        assert "token" not in serialized
        assert "credential" not in serialized
        assert "codex_home" not in serialized
