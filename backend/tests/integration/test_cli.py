import json

import pytest

from codex_flow.cli.main import main
from codex_flow.codex_adapter.fake import FakeCodexAdapter


def test_run_loads_workflow_fixture_into_defaulted_database(tmp_path, capsys, monkeypatch) -> None:
    workflow = tmp_path / "workflow.json"
    workflow.write_text(
        json.dumps(
            {
                "id": "workflow",
                "name": "Workflow",
                "tasks": [{"id": "A", "name": "A", "prompt": "A", "cwd": "."}],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("codex_flow.cli.main.SdkCodexAdapter", FakeCodexAdapter)

    assert main(["run", str(workflow), "--db", str(tmp_path / "flow.sqlite3")]) == 0
    assert "run completed:" in capsys.readouterr().out


@pytest.mark.parametrize(
    "arguments",
    [["status", "run"], ["retry", "run", "task"], ["cancel", "run", "task"], ["pause", "run"], ["resume", "run"]],
)
def test_commands_have_headless_entrypoints(arguments: list[str]) -> None:
    assert main(arguments) == 0
