import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest


def _runner_command(workflow: Path, database: Path) -> list[str]:
    return [
        sys.executable,
        "-c",
        "from codex_flow.cli.main import main; import sys; raise SystemExit(main(sys.argv[1:]))",
        "run",
        str(workflow),
        "--db",
        str(database),
    ]


def _status_when_running(database: Path) -> str | None:
    if not database.exists():
        return None
    try:
        with sqlite3.connect(database, timeout=0.1) as connection:
            row = connection.execute("SELECT status FROM task_runs WHERE task_id = 'A'").fetchone()
    except sqlite3.OperationalError:
        return None
    return None if row is None else str(row[0])


@pytest.mark.live_codex
def test_real_restart_recovers_without_duplicate_prompt_or_downstream_start(tmp_path) -> None:
    database = tmp_path / "flow.sqlite3"
    workflow = tmp_path / "workflow.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    workflow.write_text(
        json.dumps(
            {
                "id": "restart-workflow",
                "name": "Restart workflow",
                "tasks": [
                    {
                        "id": "A",
                        "name": "A",
                        "prompt": "Run a command that sleeps for 60 seconds, then stop.",
                        "cwd": str(workspace),
                    },
                    {
                        "id": "B",
                        "name": "B",
                        "prompt": "Create B.txt containing exactly B_DONE, then stop.",
                        "cwd": str(workspace),
                        "dependencies": ["A"],
                    },
                ],
                "edges": [{"source_task_id": "A", "target_task_id": "B"}],
            }
        ),
        encoding="utf-8",
    )
    backend_root = Path(__file__).parents[2]
    environment = {**os.environ, "PYTHONPATH": str(backend_root / "src")}
    process = subprocess.Popen(
        _runner_command(workflow, database),
        cwd=backend_root,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and _status_when_running(database) != "RUNNING":
            time.sleep(0.2)
        assert _status_when_running(database) == "RUNNING"
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)

    restarted = subprocess.run(
        _runner_command(workflow, database),
        cwd=backend_root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert restarted.returncode == 0, restarted.stderr
    with sqlite3.connect(database) as connection:
        task_rows = dict(connection.execute("SELECT task_id, status FROM task_runs"))
        attempts = connection.execute("SELECT count(*) FROM attempts WHERE task_run_id = (SELECT id FROM task_runs WHERE task_id = 'A')").fetchone()[0]
        run_count = connection.execute("SELECT count(*) FROM workflow_runs").fetchone()[0]
    assert task_rows == {"A": "NEEDS_ATTENTION", "B": "BLOCKED"}
    assert attempts == 1
    assert run_count == 1
    assert not (workspace / "B.txt").exists()
