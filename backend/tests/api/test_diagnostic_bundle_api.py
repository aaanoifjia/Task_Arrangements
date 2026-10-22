import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def test_authorized_diagnostic_bundle_download_is_allowlisted(tmp_path: Path) -> None:
    app = create_app(
        ServiceConfig.from_db_path(tmp_path / "diagnostics.sqlite3", token="diagnostic-token", desktop_mode=True),
        adapter=FakeCodexAdapter(),
    )

    with TestClient(app) as client:
        response = client.get("/api/system/diagnostics/bundle", headers={"Authorization": "Bearer diagnostic-token"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == 'attachment; filename="codex-flow-diagnostics.zip"'
    with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
        assert set(bundle.namelist()) == {
            "diagnostics/summary.json",
            "diagnostics/metadata.json",
            "logs/redacted.log",
        }
        assert b"diagnostics.sqlite3" not in bundle.read("diagnostics/summary.json")


def test_unauthorized_diagnostic_bundle_download_fails_closed(tmp_path: Path) -> None:
    app = create_app(
        ServiceConfig.from_db_path(tmp_path / "diagnostics.sqlite3", token="diagnostic-token", desktop_mode=True),
        adapter=FakeCodexAdapter(),
    )

    with TestClient(app) as client:
        response = client.get("/api/system/diagnostics/bundle")

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "UNAUTHORIZED"
