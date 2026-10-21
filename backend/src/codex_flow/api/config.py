"""Deterministic configuration for the local API service."""

from dataclasses import dataclass
from pathlib import Path

TAURI_WEBVIEW_ORIGINS = ("http://tauri.localhost",)


@dataclass(frozen=True)
class ServiceConfig:
    db_path: Path
    event_poll_interval_seconds: float = 0.25
    token: str | None = None
    desktop_mode: bool = False
    cors_origins: tuple[str, ...] = TAURI_WEBVIEW_ORIGINS

    @classmethod
    def default(cls) -> "ServiceConfig":
        return cls(db_path=Path.cwd() / ".codex-flow.sqlite3")

    @classmethod
    def from_db_path(
        cls,
        db_path: Path | None = None,
        token: str | None = None,
        desktop_mode: bool = False,
        cors_origins: tuple[str, ...] = TAURI_WEBVIEW_ORIGINS,
    ) -> "ServiceConfig":
        return cls(
            db_path=db_path or (Path.cwd() / ".codex-flow.sqlite3"),
            token=token,
            desktop_mode=desktop_mode,
            cors_origins=cors_origins,
        )
