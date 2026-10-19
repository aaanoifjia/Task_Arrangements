"""Standard-library CLI surface for the headless MVP."""

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.sdk import SdkCodexAdapter
from codex_flow.domain.models import WorkflowDefinition
from codex_flow.runtime.runner import DurableRunner
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-flow")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("workflow", type=Path)
    run.add_argument("--db", type=Path, default=Path(".codex-flow.sqlite3"))
    for name in ("status", "pause", "resume"):
        command = commands.add_parser(name)
        command.add_argument("run_id")
    for name in ("retry", "cancel"):
        command = commands.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("task_id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "run":
        workflow = WorkflowDefinition.model_validate(json.loads(arguments.workflow.read_text(encoding="utf-8")))
        adapter = SdkCodexAdapter()
        try:
            runner = DurableRunner(StorageRepositories(open_database(arguments.db)), cast(CodexAdapter, adapter))
            run_id = asyncio.run(runner.run(workflow))
        finally:
            asyncio.run(adapter.close())
        print(f"run completed: {run_id}")
    elif arguments.command in {"retry", "cancel"}:
        print(f"{arguments.command} requested: {arguments.run_id}/{arguments.task_id}")
    else:
        print(f"{arguments.command} requested: {arguments.run_id}")
    return 0
