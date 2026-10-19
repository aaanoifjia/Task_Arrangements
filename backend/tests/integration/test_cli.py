import json

import pytest

from codex_flow.cli.main import main


def test_run_loads_workflow_fixture(tmp_path, capsys) -> None:
    workflow = tmp_path / "workflow.json"
    workflow.write_text(json.dumps({"id": "workflow"}), encoding="utf-8")

    assert main(["run", str(workflow)]) == 0
    assert "workflow" in capsys.readouterr().out


@pytest.mark.parametrize(
    "arguments",
    [["status", "run"], ["retry", "run", "task"], ["cancel", "run", "task"], ["pause", "run"], ["resume", "run"]],
)
def test_commands_have_headless_entrypoints(arguments: list[str]) -> None:
    assert main(arguments) == 0
