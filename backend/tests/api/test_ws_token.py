"""WebSocket token validation tests for desktop mode."""

from pathlib import Path

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from codex_flow.api.app import create_app
from codex_flow.api.config import ServiceConfig


@pytest.mark.parametrize("query", ["", "?token=wrong"])
def test_websocket_rejects_missing_or_invalid_token(query: str, tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "ws-token.sqlite3", token="secret"))

    with TestClient(app) as client, pytest.raises(WebSocketDisconnect) as error, client.websocket_connect(
        f"/ws/runs/missing{query}"
    ):
        pass

    assert error.value.code == 1008
    assert error.value.reason == "unauthorized"


def test_websocket_with_valid_token_reaches_run_validation(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "ws-token.sqlite3", token="secret"))

    with TestClient(app) as client, client.websocket_connect(
        "/ws/runs/missing?token=secret"
    ) as websocket, pytest.raises(WebSocketDisconnect) as error:
        websocket.receive_json()

    assert error.value.code == 1008
    assert error.value.reason == "run not found"
