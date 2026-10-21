import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig


def test_explicit_db_path_is_migrated_and_closed_on_shutdown(tmp_path: Path) -> None:
    database = tmp_path / "service.sqlite3"
    app = create_app(ServiceConfig.from_db_path(database))

    with TestClient(app):
        assert database.exists()
        with sqlite3.connect(database) as connection:
            assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
    with pytest.raises(sqlite3.ProgrammingError):
        app.state.connection.execute("SELECT 1")


def test_default_path_is_current_working_directory_relative(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    config = ServiceConfig.default()

    assert config.db_path == tmp_path / ".codex-flow.sqlite3"
