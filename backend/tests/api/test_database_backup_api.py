import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def workflow_payload() -> dict[str, object]:
    return {
        "id": "api-backup-workflow",
        "name": "API backup workflow",
        "tasks": [{"id": "A", "name": "A", "prompt": "safe", "cwd": "."}],
        "edges": [],
    }


def test_authorized_backup_download_is_valid_sqlite_and_preserves_source(tmp_path: Path) -> None:
    source_path = tmp_path / "source.sqlite3"
    app = create_app(
        ServiceConfig.from_db_path(source_path, token="backup-token", desktop_mode=True),
        adapter=FakeCodexAdapter(),
    )

    with TestClient(app) as client:
        headers = {"Authorization": "Bearer backup-token"}
        assert client.post("/api/workflows", json=workflow_payload(), headers=headers).status_code == 201
        response = client.get("/api/system/database/backup", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-disposition"] == 'attachment; filename="codex-flow-backup.sqlite3"'
    backup_path = tmp_path / "downloaded.sqlite3"
    backup_path.write_bytes(response.content)
    copied = sqlite3.connect(backup_path)
    try:
        assert copied.execute("PRAGMA user_version").fetchone()[0] == 3
        assert copied.execute("SELECT id FROM workflows").fetchone()[0] == "api-backup-workflow"
    finally:
        copied.close()
    source = sqlite3.connect(source_path)
    try:
        assert source.execute("SELECT id FROM workflows").fetchone()[0] == "api-backup-workflow"
    finally:
        source.close()


def test_unauthorized_backup_download_fails_closed(tmp_path: Path) -> None:
    app = create_app(
        ServiceConfig.from_db_path(tmp_path / "source.sqlite3", token="backup-token", desktop_mode=True),
        adapter=FakeCodexAdapter(),
    )

    with TestClient(app) as client:
        response = client.get("/api/system/database/backup")

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "UNAUTHORIZED"
