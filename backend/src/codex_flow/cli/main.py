"""Standard-library CLI surface for the headless MVP."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-flow")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("workflow", type=Path)
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
        workflow = json.loads(arguments.workflow.read_text(encoding="utf-8"))
        print(f"run requested: {workflow['id']}")
    elif arguments.command in {"retry", "cancel"}:
        print(f"{arguments.command} requested: {arguments.run_id}/{arguments.task_id}")
    else:
        print(f"{arguments.command} requested: {arguments.run_id}")
    return 0
