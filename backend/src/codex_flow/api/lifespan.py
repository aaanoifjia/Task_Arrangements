"""FastAPI lifespan resource management for the local SQLite store."""

import sqlite3
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI

from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.domain.models import WorkflowDefinition
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.recovery import StartupReconciler
from codex_flow.storage.repositories import StorageRepositories

AdapterFactory = Callable[[], CodexAdapter]


def default_adapter_factory() -> CodexAdapter:
    """Construct the production adapter lazily, outside API module imports."""
    from codex_flow.codex_adapter.sdk import SdkCodexAdapter

    return cast(CodexAdapter, SdkCodexAdapter())


@asynccontextmanager
async def lifespan(
    app: FastAPI, config: ServiceConfig, adapter_factory: AdapterFactory | None = None
) -> AsyncIterator[None]:
    connection = open_database(config.db_path)
    app.state.connection = connection
    repositories = StorageRepositories(connection)
    app.state.repositories = repositories
    adapter = (adapter_factory or default_adapter_factory)()
    app.state.adapter = adapter
    await StartupReconciler(connection, adapter).reconcile()
    runtime = RuntimeManager(repositories, adapter)
    for row in repositories.load_active_runs():
        runtime.restore_workflow(
            str(row["id"]), WorkflowDefinition.model_validate_json(row["snapshot_json"])
        )
    app.state.runtime = runtime
    try:
        yield
    finally:
        await runtime.shutdown()
        await adapter.close()
        connection.close()


def get_connection(app: FastAPI) -> sqlite3.Connection:
    """Return the explicitly opened application connection for typed callers."""
    return cast(sqlite3.Connection, app.state.connection)


def get_repositories(app: FastAPI) -> StorageRepositories:
    return cast(StorageRepositories, app.state.repositories)
