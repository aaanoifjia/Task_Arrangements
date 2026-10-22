import sqlite3
from pathlib import Path

from codex_flow.application.diagnostics import DiagnosticService


class FakeRepository:
    def __init__(self) -> None:
        self._runs = [{"id": "run-1"}, {"id": "run-2"}]
        self._events = {
            "run-1": [
                {"event_type": "TURN_FAILED", "payload": "secret prompt body"},
                {"event_type": "SUCCESS"},
            ],
            "run-2": [{"event_type": "TRANSPORT_ERROR", "token": "secret-token"}],
        }

    def load_active_runs(self) -> list[sqlite3.Row]:
        return self._runs  # type: ignore[return-value]

    def load_events_for_run(self, workflow_run_id: str) -> list[sqlite3.Row]:
        return self._events.get(workflow_run_id, [])  # type: ignore[return-value]


class FakeRuntime:
    def active_count(self) -> int:
        return 3


class FakeConfig:
    db_path = Path(r"C:\private\diagnostics.sqlite3")


def test_diagnostic_service_gathers_bounded_secret_free_metadata() -> None:
    summary = DiagnosticService(
        FakeRepository(),
        FakeRuntime(),
        FakeConfig(),
        schema_version=3,
        log_directory=Path(r"C:\private\logs"),
        app_version="app-test",
        backend_version="backend-test",
    ).collect()

    assert summary.app_version == "app-test"
    assert summary.backend_version == "backend-test"
    assert summary.db_schema_version == 3
    assert summary.db_path_category == "configured"
    assert summary.log_directory_category == "configured"
    assert summary.active_run_count == 2
    assert summary.active_task_count == 3
    assert summary.recent_error_event_types == ["TURN_FAILED", "TRANSPORT_ERROR"]
    serialized = summary.model_dump_json().lower()
    assert "prompt" not in serialized
    assert "token" not in serialized
    assert "diagnostics.sqlite3" not in serialized


def test_diagnostic_service_preserves_unavailable_schema_fact() -> None:
    class EmptyRepository(FakeRepository):
        def load_active_runs(self) -> list[sqlite3.Row]:
            return []

    summary = DiagnosticService(
        EmptyRepository(),
        FakeRuntime(),
        FakeConfig(),
        schema_version=None,
        log_directory=None,
    ).collect()

    assert summary.db_schema_version is None
    assert summary.active_run_count == 0
    assert summary.recent_error_event_types == []
