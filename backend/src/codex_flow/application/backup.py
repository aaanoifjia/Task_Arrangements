"""User-requested SQLite online backup primitives."""

import sqlite3
from pathlib import Path


def create_database_backup(source: sqlite3.Connection, output_path: Path) -> Path:
    """Create a consistent SQLite copy without mutating the source connection."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    target = sqlite3.connect(output_path)
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
    return output_path
