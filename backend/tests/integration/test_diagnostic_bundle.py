import json
import zipfile
from pathlib import Path

from codex_flow.application.diagnostic_bundle import create_diagnostic_bundle
from codex_flow.application.diagnostics import build_diagnostic_summary


def summary():
    return build_diagnostic_summary(
        app_version="0.1.0",
        backend_version="0.1.0",
        db_schema_version=3,
        db_path=Path(r"C:\private\workflow.sqlite3"),
        active_run_count=1,
        active_task_count=2,
        event_types=["TURN_FAILED"],
        log_directory=Path(r"C:\private\logs"),
        os_name="TestOS",
        os_release="1.0",
        python_version="3.11.9",
    )


def test_diagnostic_bundle_has_allowlist_redaction_and_reproducible_bytes(tmp_path: Path) -> None:
    logs = [
        "authorization: bearer secret-token",
        "prompt=private prompt body",
        "error=visible failure class",
    ]
    manifest = [{"filename": "sidecar.exe", "size": 12, "sha256": "abc", "path": r"C:\private\sidecar.exe"}]
    first = create_diagnostic_bundle(tmp_path / "first.zip", summary(), logs=logs, artifact_manifest=manifest)
    second = create_diagnostic_bundle(tmp_path / "second.zip", summary(), logs=logs, artifact_manifest=manifest)

    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as bundle:
        assert bundle.namelist() == [
            "diagnostics/summary.json",
            "diagnostics/metadata.json",
            "logs/redacted.log",
            "artifacts/manifest.json",
        ]
        log_text = bundle.read("logs/redacted.log").decode()
        assert "secret-token" not in log_text
        assert "private prompt body" not in log_text
        assert "visible failure class" in log_text
        assert "workflow.sqlite3" not in bundle.read("diagnostics/summary.json").decode()
        assert "sidecar.exe" in bundle.read("artifacts/manifest.json").decode()
        assert "private" not in bundle.read("artifacts/manifest.json").decode()


def test_diagnostic_bundle_excludes_database_environment_and_raw_content(tmp_path: Path) -> None:
    output = create_diagnostic_bundle(
        tmp_path / "diagnostics.zip",
        summary(),
        logs=["token=secret prompt=do not include"],
    )

    with zipfile.ZipFile(output) as bundle:
        names = set(bundle.namelist())
        assert "database.sqlite3" not in names
        assert "environment.json" not in names
        combined = b"".join(bundle.read(name) for name in names)
        assert b"secret" not in combined
        assert b"do not include" not in combined
        assert json.loads(bundle.read("diagnostics/metadata.json"))["bundle_schema_version"] == 1
