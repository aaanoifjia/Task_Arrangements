import sqlite3
import threading
import time
from pathlib import Path

from codex_flow.storage.db import SQLITE_BUSY_TIMEOUT_MS, open_database


def test_sqlite_connection_guards_are_enabled(tmp_path: Path) -> None:
    connection = open_database(tmp_path / "flow.sqlite3")

    assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == SQLITE_BUSY_TIMEOUT_MS


def test_concurrent_write_waits_for_short_lock_and_commits(tmp_path: Path) -> None:
    database = tmp_path / "flow.sqlite3"
    holder_ready = threading.Event()
    release_holder = threading.Event()
    errors: list[sqlite3.Error] = []

    def hold_write_lock() -> None:
        connection = open_database(database)
        try:
            connection.execute("BEGIN IMMEDIATE")
            holder_ready.set()
            release_holder.wait(2)
            connection.commit()
        except sqlite3.Error as error:  # pragma: no cover - surfaced below
            errors.append(error)
        finally:
            connection.close()

    def write_while_locked() -> None:
        connection = open_database(database)
        try:
            holder_ready.wait(2)
            with connection:
                connection.execute(
                    "INSERT INTO workflows(id, name, definition_json, created_at) VALUES (?, ?, ?, ?)",
                    ("workflow", "Workflow", "{}", "now"),
                )
        except sqlite3.Error as error:  # pragma: no cover - surfaced below
            errors.append(error)
        finally:
            connection.close()

    holder = threading.Thread(target=hold_write_lock)
    writer = threading.Thread(target=write_while_locked)
    holder.start()
    assert holder_ready.wait(2)
    writer.start()
    time.sleep(0.05)
    release_holder.set()
    holder.join(2)
    writer.join(2)

    assert not errors
    connection = open_database(database)
    assert connection.execute("SELECT id FROM workflows").fetchone()[0] == "workflow"
