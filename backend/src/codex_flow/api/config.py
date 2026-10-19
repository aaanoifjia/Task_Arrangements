"""Deterministic configuration for the local API service."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceConfig:
    db_path: Path
    event_poll_interval_seconds: float = 0.25

    @classmethod
    def default(cls) -> "ServiceConfig":
        return cls(db_path=Path.cwd() / ".codex-flow.sqlite3")

    @classmethod
    def from_db_path(cls, db_path: Path | None = None) -> "ServiceConfig":
        return cls(db_path=db_path or (Path.cwd() / ".codex-flow.sqlite3"))
