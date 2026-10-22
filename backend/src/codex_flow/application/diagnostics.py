"""SDK-independent, secret-free diagnostic summary primitives."""

import platform
import sys
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, Field

DIAGNOSTIC_ERROR_EVENT_TYPES = frozenset(
    {
        "ATTENTION_REQUIRED",
        "MANUAL_ACTION_REJECTED",
        "TASK_FAILED",
        "TASK_TIMEOUT",
        "TRANSPORT_ERROR",
        "TURN_FAILED",
    }
)
MAX_RECENT_ERROR_EVENT_TYPES = 20


class DiagnosticSummary(BaseModel):
    """Bounded operational facts that never contain workflow content or secrets."""

    app_version: str
    backend_version: str
    os_name: str
    os_release: str
    python_version: str
    db_schema_version: int | None
    db_path_category: str
    active_run_count: int
    active_task_count: int
    recent_error_event_types: list[str] = Field(default_factory=list)
    log_directory_category: str


def path_category(path: Path | None) -> str:
    """Return whether a path is configured without exposing the path itself."""

    return "configured" if path is not None else "unavailable"


def recent_error_event_types(event_types: Iterable[str]) -> list[str]:
    """Keep only known error labels, deduplicate, and bound the recent list."""

    unique = list(dict.fromkeys(event_type for event_type in event_types if event_type in DIAGNOSTIC_ERROR_EVENT_TYPES))
    return unique[-MAX_RECENT_ERROR_EVENT_TYPES:]


def build_diagnostic_summary(
    *,
    app_version: str,
    backend_version: str,
    db_schema_version: int | None,
    db_path: Path | None,
    active_run_count: int,
    active_task_count: int,
    event_types: Iterable[str],
    log_directory: Path | None,
    os_name: str | None = None,
    os_release: str | None = None,
    python_version: str | None = None,
) -> DiagnosticSummary:
    """Build a diagnostic summary from explicit facts and safe host metadata."""

    return DiagnosticSummary(
        app_version=app_version,
        backend_version=backend_version,
        os_name=os_name or platform.system(),
        os_release=os_release or platform.release(),
        python_version=python_version or platform.python_version() or sys.version.split()[0],
        db_schema_version=db_schema_version,
        db_path_category=path_category(db_path),
        active_run_count=active_run_count,
        active_task_count=active_task_count,
        recent_error_event_types=recent_error_event_types(event_types),
        log_directory_category=path_category(log_directory),
    )
