import json
from pathlib import Path

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def prepare_run(database: Path, run_id: str = "run") -> str:
    repository = StorageRepositories(open_database(database))
    repository._connection.execute("INSERT INTO workflows VALUES (?, ?, ?, ?)", ("workflow", "Workflow", json.dumps({}), "now"))
    repository._connection.execute(
        "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at, paused, paused_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, "workflow", "{}", "SUCCESS", "now", 0, None),
    )
    repository._connection.execute("INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) VALUES (?, ?, ?, ?, ?)", ("task", run_id, "A", "SUCCESS", "now"))
    repository.append_event("TURN_COMPLETED", {}, workflow_run_id=run_id, task_run_id="task")
    repository._connection.commit()
    repository._connection.close()
    return run_id


def test_websocket_sends_snapshot_and_durable_event_and_reconnects(tmp_path: Path) -> None:
    database = tmp_path / "api.sqlite3"
    run_id = prepare_run(database)
    with TestClient(create_app(ServiceConfig.from_db_path(database))) as client:
        with client.websocket_connect(f"/ws/runs/{run_id}") as socket:
            first = socket.receive_json()
            second = socket.receive_json()
        assert {first["kind"], second["kind"]} == {"event", "snapshot"}

        event_message = first if first["kind"] == "event" else second
        with client.websocket_connect(f"/ws/runs/{run_id}?after={event_message['payload']['id']}") as socket:
            resumed = socket.receive_json()
        assert resumed["kind"] == "snapshot"


def test_missing_run_closes_websocket_deterministically(tmp_path: Path) -> None:
    app = create_app(ServiceConfig.from_db_path(tmp_path / "api.sqlite3"))

    with (
        TestClient(app) as client,
        pytest.raises(WebSocketDisconnect) as error,
        client.websocket_connect("/ws/runs/missing") as socket,
    ):
        socket.receive_json()
    assert error.value.code == 1008
