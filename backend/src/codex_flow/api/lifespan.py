"""FastAPI lifespan resource management for the local SQLite store."""

import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI

from codex_flow.api.config import ServiceConfig
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


@asynccontextmanager
async def lifespan(app: FastAPI, config: ServiceConfig) -> AsyncIterator[None]:
    connection = open_database(config.db_path)
    app.state.connection = connection
    app.state.repositories = StorageRepositories(connection)
    try:
        yield
    finally:
        connection.close()


def get_connection(app: FastAPI) -> sqlite3.Connection:
    """Return the explicitly opened application connection for typed callers."""
    return cast(sqlite3.Connection, app.state.connection)


def get_repositories(app: FastAPI) -> StorageRepositories:
    return cast(StorageRepositories, app.state.repositories)
