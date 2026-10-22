"""SDK-independent, secret-free diagnostic summary primitives."""

import platform
import sqlite3
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from codex_flow import __version__

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


class DiagnosticRepository(Protocol):
    def load_active_runs(self) -> list[sqlite3.Row]: ...

    def load_events_for_run(self, workflow_run_id: str) -> list[sqlite3.Row]: ...


class DiagnosticRuntime(Protocol):
    active_count: int


class DiagnosticConfig(Protocol):
    db_path: Path


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


class DiagnosticService:
    """Gather bounded operational metadata from durable and process-local sources."""

    def __init__(
        self,
        repository: DiagnosticRepository,
        runtime: DiagnosticRuntime,
        config: DiagnosticConfig,
        *,
        schema_version: int | None,
        log_directory: Path | None,
        app_version: str = __version__,
        backend_version: str = __version__,
    ) -> None:
        self._repository = repository
        self._runtime = runtime
        self._config = config
        self._schema_version = schema_version
        self._log_directory = log_directory
        self._app_version = app_version
        self._backend_version = backend_version

    def collect(self) -> DiagnosticSummary:
        active_runs = self._repository.load_active_runs()
        event_types: list[str] = []
        for row in active_runs:
            run_id = str(row["id"])
            event_types.extend(str(event["event_type"]) for event in self._repository.load_events_for_run(run_id)[-100:])
        return build_diagnostic_summary(
            app_version=self._app_version,
            backend_version=self._backend_version,
            db_schema_version=self._schema_version,
            db_path=self._config.db_path,
            active_run_count=len(active_runs),
            active_task_count=self._runtime.active_count,
            event_types=event_types[-100:],
            log_directory=self._log_directory,
        )
