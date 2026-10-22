"""Desktop sidecar token renewal and authorization boundaries."""

from pathlib import Path

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def _workflow_payload(cwd: Path) -> dict[str, object]:
    return {
        "id": "token-relaunch-workflow",
        "name": "Token Relaunch Workflow",
        "tasks": [{"id": "A", "name": "A", "prompt": "A", "cwd": str(cwd)}],
        "edges": [],
    }


def test_relaunch_renews_rest_and_websocket_token_without_persistence(tmp_path: Path) -> None:
    database = tmp_path / "token-relaunch.sqlite3"
    old_token = "old-sidecar-session-token"
    new_token = "new-sidecar-session-token"

    with TestClient(
        create_app(
            ServiceConfig.from_db_path(database, token=old_token),
            adapter=FakeCodexAdapter(),
        )
    ) as client:
        created = client.post(
            "/api/workflows",
            json=_workflow_payload(tmp_path),
            headers={"Authorization": f"Bearer {old_token}"},
        )
        assert created.status_code == 201

    with TestClient(
        create_app(
            ServiceConfig.from_db_path(database, token=new_token),
            adapter=FakeCodexAdapter(),
        )
    ) as client:
        assert client.get(
            "/api/workflows", headers={"Authorization": f"Bearer {old_token}"}
        ).status_code == 401
        assert client.get(
            "/api/workflows", headers={"Authorization": f"Bearer {new_token}"}
        ).status_code == 200

        started = client.post(
            "/api/workflows/token-relaunch-workflow/runs",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert started.status_code == 202
        run_id = started.json()["run_id"]
        for _ in range(10):
            if client.get(
                f"/api/runs/{run_id}",
                headers={"Authorization": f"Bearer {new_token}"},
            ).json()["status"] == "SUCCESS":
                break

        with pytest.raises(WebSocketDisconnect), client.websocket_connect(
            f"/ws/runs/{run_id}?token={old_token}"
        ):
            pass

        with client.websocket_connect(f"/ws/runs/{run_id}?token={new_token}") as socket:
            assert socket.receive_json()["kind"] == "snapshot"

    for path in tmp_path.rglob("*"):
        if path.is_file():
            contents = path.read_bytes()
            assert old_token.encode() not in contents
            assert new_token.encode() not in contents
