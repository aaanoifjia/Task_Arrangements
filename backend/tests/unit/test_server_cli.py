"""Tests for the production server entrypoint."""

import sys
import types
from pathlib import Path

import pytest

from codex_flow import server


def test_server_defaults_to_loopback_and_local_database() -> None:
    options = server.parse_args([])

    assert options.host == "127.0.0.1"
    assert options.port == 8000
    assert options.db_path == Path(".codex-flow.sqlite3")
    assert options.token is None
    assert options.log_dir is None


def test_server_accepts_explicit_desktop_options() -> None:
    options = server.parse_args(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "43127",
            "--db-path",
            "C:/Codex Flow/data.sqlite3",
            "--token",
            "local-token",
            "--log-dir",
            "C:/Codex Flow/logs",
        ]
    )

    assert options.port == 43127
    assert options.db_path == Path("C:/Codex Flow/data.sqlite3")
    assert options.token == "local-token"
    assert options.log_dir == Path("C:/Codex Flow/logs")


def test_import_does_not_start_uvicorn(monkeypatch) -> None:
    calls: list[object] = []
    fake_uvicorn = types.ModuleType("uvicorn")
    fake_uvicorn.run = lambda *args, **kwargs: calls.append((args, kwargs))
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    # The module is already imported above; reloading exercises its import path.
    import importlib

    importlib.reload(server)

    assert calls == []


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_desktop_mode_accepts_loopback_hosts(host: str) -> None:
    server.validate_bind_host(host)


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.20"])
def test_desktop_mode_rejects_wildcard_and_lan_hosts(host: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        server.validate_bind_host(host)
