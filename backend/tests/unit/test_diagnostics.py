from pathlib import Path

from codex_flow.application.diagnostics import (
    build_diagnostic_summary,
    recent_error_event_types,
)


def test_diagnostic_summary_contains_bounded_operational_facts_only() -> None:
    summary = build_diagnostic_summary(
        app_version="0.1.0",
        backend_version="0.1.0",
        db_schema_version=3,
        db_path=Path(r"C:\private\workflow.sqlite3"),
        active_run_count=2,
        active_task_count=3,
        event_types=["TURN_FAILED", "SUCCESS", "TRANSPORT_ERROR", "TURN_FAILED"],
        log_directory=Path(r"C:\private\logs"),
        os_name="TestOS",
        os_release="1.2",
        python_version="3.11.9",
    )

    body = summary.model_dump()
    assert body == {
        "app_version": "0.1.0",
        "backend_version": "0.1.0",
        "os_name": "TestOS",
        "os_release": "1.2",
        "python_version": "3.11.9",
        "db_schema_version": 3,
        "db_path_category": "configured",
        "active_run_count": 2,
        "active_task_count": 3,
        "recent_error_event_types": ["TURN_FAILED", "TRANSPORT_ERROR"],
        "log_directory_category": "configured",
    }
    serialized = str(body).lower()
    assert "prompt" not in serialized
    assert "token" not in serialized
    assert "workflow.sqlite3" not in serialized


def test_diagnostic_summary_reports_unavailable_optional_facts_without_guessing() -> None:
    summary = build_diagnostic_summary(
        app_version="0.1.0",
        backend_version="0.1.0",
        db_schema_version=None,
        db_path=None,
        active_run_count=0,
        active_task_count=0,
        event_types=[],
        log_directory=None,
        os_name="TestOS",
        os_release="unknown",
        python_version="3.11.9",
    )

    assert summary.db_schema_version is None
    assert summary.db_path_category == "unavailable"
    assert summary.log_directory_category == "unavailable"


def test_recent_error_event_types_are_filtered_and_bounded() -> None:
    event_types = ["SUCCESS"] * 3 + ["TURN_FAILED", "UNKNOWN"] * 15

    result = recent_error_event_types(event_types)

    assert result == ["TURN_FAILED"]
