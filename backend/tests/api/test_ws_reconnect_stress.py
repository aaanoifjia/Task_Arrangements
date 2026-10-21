import json
from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def prepare_run(database: Path, event_count: int = 64) -> tuple[str, list[str]]:
    repository = StorageRepositories(open_database(database))
    repository._connection.execute(
        "INSERT INTO workflows VALUES (?, ?, ?, ?)",
        ("workflow", "Workflow", json.dumps({}), "now"),
    )
    repository._connection.execute(
        "INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at, paused, paused_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("run", "workflow", "{}", "SUCCESS", "now", 0, None),
    )
    repository._connection.execute(
        "INSERT INTO task_runs(id, workflow_run_id, task_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
        ("task", "run", "A", "SUCCESS", "now"),
    )
    event_ids = [
        repository.append_event(
            "STRESS_EVENT", {"sequence": sequence}, workflow_run_id="run", task_run_id="task"
        )
        for sequence in range(event_count)
    ]
    repository._connection.commit()
    repository._connection.close()
    return "run", event_ids


def test_reconnect_storm_resumes_cursor_without_duplicate_events(tmp_path: Path) -> None:
    database = tmp_path / "api.sqlite3"
    run_id, expected_ids = prepare_run(database)
    received_ids: list[str] = []
    cursor: str | None = None

    with TestClient(create_app(ServiceConfig.from_db_path(database))) as client:
        for _ in range(40):
            query = f"?after={cursor}" if cursor is not None else ""
            with client.websocket_connect(f"/ws/runs/{run_id}{query}") as socket:
                for _ in range(5):
                    message = socket.receive_json()
                    if message["kind"] != "event":
                        continue
                    cursor = str(message["payload"]["id"])
                    received_ids.append(cursor)
                if len(received_ids) == len(expected_ids):
                    break

    assert received_ids == expected_ids
    assert len(received_ids) == len(set(received_ids))
