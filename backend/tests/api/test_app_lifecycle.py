from pathlib import Path

from fastapi.testclient import TestClient

from codex_flow.api import create_app
from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexThreadRef, CodexThreadSnapshot
from codex_flow.storage.db import open_database


class TrackingAdapter(FakeCodexAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.lifecycle: list[str] = []

    async def read_thread(self, thread: CodexThreadRef) -> CodexThreadSnapshot:
        self.lifecycle.append("read_thread")
        return await super().read_thread(thread)

    async def close(self) -> None:
        self.lifecycle.append("close")
        await super().close()


def seed_recoverable_task(database: Path) -> None:
    connection = open_database(database)
    connection.executescript(
        """
        INSERT INTO workflows VALUES ('workflow', 'Workflow', '{}', 'now');
        INSERT INTO workflow_runs(id, workflow_id, snapshot_json, status, created_at, paused, paused_at)
        VALUES ('run', 'workflow', '{"id":"workflow","name":"Workflow","description":null,"tasks":[],"edges":[]}', 'RUNNING', 'now', 0, NULL);
        INSERT INTO task_runs(id, workflow_run_id, task_id, status, thread_id, created_at)
        VALUES ('task', 'run', 'A', 'RUNNING', 'thread', 'now');
        """
    )
    connection.commit()
    connection.close()


def test_startup_recovery_precedes_requests_and_closes_adapter_once(tmp_path: Path) -> None:
    database = tmp_path / "lifecycle.sqlite3"
    seed_recoverable_task(database)
    adapter = TrackingAdapter()

    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter=adapter)) as client:
        assert adapter.lifecycle == ["read_thread"]
        response = client.get("/api/runs/run")
        assert response.status_code == 200
        assert client.app.state.runtime.active_count == 0

    assert adapter.lifecycle == ["read_thread", "close"]
    connection = open_database(database)
    assert connection.execute("SELECT status FROM task_runs WHERE id = 'task'").fetchone()[0] == "NEEDS_ATTENTION"
    connection.close()


def test_injected_factory_reopens_same_database_without_live_sdk(tmp_path: Path) -> None:
    database = tmp_path / "reopen.sqlite3"
    first = TrackingAdapter()
    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter_factory=lambda: first)) as client:
        assert client.get("/api/workflows").status_code == 200
    second = TrackingAdapter()
    with TestClient(create_app(ServiceConfig.from_db_path(database), adapter_factory=lambda: second)) as client:
        assert client.get("/api/workflows").status_code == 200
    assert first.calls[-1] == "close"
    assert second.calls[-1] == "close"
