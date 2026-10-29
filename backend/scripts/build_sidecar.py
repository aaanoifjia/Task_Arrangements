"""Generate and run the reproducible PyInstaller sidecar build command."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = BACKEND_ROOT / "codex_flow_sidecar.spec"
DEFAULT_OUTPUT_ROOT = BACKEND_ROOT.parent / "desktop" / "sidecar"
TAURI_BINARY_ROOT = BACKEND_ROOT.parent / "desktop" / "src-tauri" / "binaries"
TAURI_SIDECAR_NAME = "codex-flow-server-x86_64-pc-windows-msvc.exe"


def preserve_existing(path: Path) -> None:
    """Move a prior generated binary aside so Windows can replace it safely."""
    if not path.exists():
        return
    backup = path.with_name(f"{path.name}.previous-{os.getpid()}")
    path.replace(backup)


def build_command(output_root: Path = DEFAULT_OUTPUT_ROOT) -> list[str]:
    """Return the deterministic command used for a clean sidecar build."""
    return [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(output_root / "dist"),
        "--workpath",
        str(output_root / "build"),
        str(SPEC_PATH),
    ]


def build_sidecar(output_root: Path = DEFAULT_OUTPUT_ROOT) -> None:
    """Run the sidecar build with the project environment's Python."""
    output_root.mkdir(parents=True, exist_ok=True)
    preserve_existing(output_root / "dist" / "codex-flow-server.exe")
    subprocess.run(build_command(output_root), cwd=BACKEND_ROOT, check=True)
    built_executable = output_root / "dist" / "codex-flow-server.exe"
    if not built_executable.is_file():
        raise FileNotFoundError(f"PyInstaller output missing: {built_executable}")
    TAURI_BINARY_ROOT.mkdir(parents=True, exist_ok=True)
    preserve_existing(TAURI_BINARY_ROOT / TAURI_SIDECAR_NAME)
    shutil.copy2(built_executable, TAURI_BINARY_ROOT / TAURI_SIDECAR_NAME)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build-sidecar")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    arguments = parser.parse_args(argv)
    build_sidecar(arguments.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
