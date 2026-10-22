"""Acceptance tests for reusable deterministic M11 fixtures."""

from __future__ import annotations

import sqlite3
import sys

import pytest
from fixtures import (
    create_app_data_dir,
    create_persisted_run,
    launch_process_probe,
    make_fake_adapter,
    make_linear_workflow,
)

from codex_flow.codex_adapter.fake import FakeScenario


@pytest.fixture
def rc_app_data_dir(tmp_path):
    return create_app_data_dir(tmp_path)


@pytest.fixture
def rc_persisted_run(rc_app_data_dir):
    workflow = make_linear_workflow(("A", "B"), cwd=str(rc_app_data_dir))
    return create_persisted_run(rc_app_data_dir / "flow.sqlite3", workflow)


def test_app_data_factory_isolated(tmp_path, rc_app_data_dir) -> None:
    first = create_app_data_dir(tmp_path, "first")
    second = create_app_data_dir(rc_app_data_dir.parent, "second")

    assert rc_app_data_dir.is_dir()
    assert first.is_dir()
    assert second.is_dir()
    assert first != second


def test_workflow_and_adapter_factories_are_fresh() -> None:
    first = make_linear_workflow(("A", "B"))
    second = make_linear_workflow(("A", "B"))
    adapter = make_fake_adapter(FakeScenario.FAILED)

    assert first == second
    assert first is not second
    assert adapter.scenario is FakeScenario.FAILED
    assert adapter.calls == []


def test_persisted_run_fixture_writes_snapshot_and_tasks(rc_persisted_run) -> None:
    connection = sqlite3.connect(rc_persisted_run.database_path)
    try:
        run = connection.execute(
            "SELECT workflow_id, snapshot_json FROM workflow_runs WHERE id = ?",
            (rc_persisted_run.run_id,),
        ).fetchone()
        task_runs = connection.execute(
            "SELECT task_id FROM task_runs WHERE workflow_run_id = ? ORDER BY task_id",
            (rc_persisted_run.run_id,),
        ).fetchall()
    finally:
        connection.close()

    assert run[0] == rc_persisted_run.workflow.id
    assert '"id": "rc-workflow"' in run[1]
    assert [row[0] for row in task_runs] == ["A", "B"]


def test_process_probe_completes_without_sleep() -> None:
    with launch_process_probe() as probe:
        assert probe.wait() == 0
        assert probe.returncode == 0


def test_process_probe_terminates_a_running_process() -> None:
    with launch_process_probe((sys.executable, "-c", "input()")) as probe:
        assert probe.returncode is None
        assert probe.terminate() is not None
