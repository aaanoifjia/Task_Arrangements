"""Offline release-candidate prerequisite contract checks."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPOSITORY_ROOT / "docs" / "rc-validation-contract.md"


def _existing_executable(name: str, *fallbacks: Path) -> Path | None:
    resolved = shutil.which(name)
    if resolved:
        return Path(resolved)
    return next((candidate for candidate in fallbacks if candidate.is_file()), None)


def _probe_version(executable: Path, *args: str) -> None:
    completed = subprocess.run(
        [str(executable), *args],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_rc_contract_is_offline_and_declares_local_prerequisites() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    assert "offline" in contract.lower()
    assert "live Codex execution" in contract
    assert "package" in contract and "downloads" in contract
    assert "manual GUI/Desktop verification" in contract
    for status in ("PASS", "BLOCKED"):
        assert status in contract
    assert "PASS" in contract


def test_existing_local_toolchain_and_tauri_inputs_pass_preflight() -> None:
    python = REPOSITORY_ROOT / ".venv" / "Scripts" / "python.exe"
    pyinstaller = REPOSITORY_ROOT / ".venv" / "Scripts" / "pyinstaller.exe"
    cargo_home = Path.home() / ".cargo" / "bin"
    rustc = _existing_executable("rustc", cargo_home / "rustc.exe")
    cargo = _existing_executable("cargo", cargo_home / "cargo.exe")
    node = _existing_executable("node")
    npm = _existing_executable("npm.cmd", Path("C:/Program Files/nodejs/npm.cmd"))
    git = _existing_executable("git")

    assert python.is_file()
    assert pyinstaller.is_file()
    assert node is not None
    assert npm is not None
    assert rustc is not None
    assert cargo is not None
    assert git is not None

    _probe_version(python, "--version")
    _probe_version(python, "-m", "PyInstaller", "--version")
    _probe_version(node, "--version")
    _probe_version(npm, "--version")
    _probe_version(rustc, "--version")
    _probe_version(cargo, "--version")
    _probe_version(git, "--version")

    required_inputs = (
        REPOSITORY_ROOT / "desktop" / "src-tauri" / "Cargo.toml",
        REPOSITORY_ROOT / "desktop" / "src-tauri" / "build.rs",
        REPOSITORY_ROOT / "desktop" / "src-tauri" / "tauri.conf.json",
        REPOSITORY_ROOT / "desktop" / "src-tauri" / "icons" / "icon.ico",
        REPOSITORY_ROOT
        / "desktop"
        / "src-tauri"
        / "binaries"
        / "codex-flow-server-x86_64-pc-windows-msvc.exe",
    )
    assert all(path.is_file() for path in required_inputs)
    assert (REPOSITORY_ROOT / "frontend" / "dist").is_dir()
