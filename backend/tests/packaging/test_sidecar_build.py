"""Deterministic checks for the Windows sidecar packaging inputs."""

import importlib.util
import inspect
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _build_module():
    module_spec = importlib.util.spec_from_file_location(
        "codex_flow_build_sidecar", BACKEND_ROOT / "scripts" / "build_sidecar.py"
    )
    assert module_spec is not None
    assert module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_build_command_uses_clean_pyinstaller_staging(tmp_path: Path) -> None:
    module = _build_module()

    command = module.build_command(tmp_path / "staging")

    assert command[1:3] == ["-m", "PyInstaller"]
    assert "--clean" in command
    assert command[-1] == str(BACKEND_ROOT / "codex_flow_sidecar.spec")
    assert str(tmp_path / "staging" / "dist") in command
    assert str(tmp_path / "staging" / "build") in command


def test_spec_collects_codex_runtime_and_sql_migrations() -> None:
    spec_text = (BACKEND_ROOT / "codex_flow_sidecar.spec").read_text(encoding="utf-8")

    assert 'collect_all("openai_codex")' in spec_text
    assert '"codex_flow/storage/migrations"' in spec_text
    assert "0001_initial.sql" not in spec_text
    assert "OPENAI_API_KEY" not in spec_text


def test_spec_builds_a_single_file_sidecar_for_tauri_external_bin() -> None:
    spec_text = (BACKEND_ROOT / "codex_flow_sidecar.spec").read_text(encoding="utf-8")

    assert "exclude_binaries=False" in spec_text
    assert "analysis.binaries" in spec_text
    assert "analysis.datas" in spec_text
    assert "COLLECT(" not in spec_text


def test_builder_expects_the_single_file_output() -> None:
    module = _build_module()

    assert 'output_root / "dist" / "codex-flow-server.exe"' in inspect.getsource(
        module.build_sidecar
    )
