"""Black-box contract probe for the built Windows sidecar executable."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import urllib.request
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SIDECAR = REPOSITORY_ROOT / "desktop" / "src-tauri" / "binaries" / "codex-flow-server-x86_64-pc-windows-msvc.exe"
RELEASE_EXECUTABLE = REPOSITORY_ROOT / "desktop" / "src-tauri" / "target" / "release" / "codex-flow-desktop.exe"


def _read_lines(stream: object, output: queue.Queue[str]) -> None:
    if not hasattr(stream, "readline"):
        return
    reader = stream  # type: ignore[assignment]
    for line in iter(reader.readline, ""):
        output.put(line)


def _get_json(url: str, token: str | None = None) -> dict[str, object]:
    request = urllib.request.Request(url)
    if token is not None:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.status == 200
        return json.loads(response.read().decode("utf-8"))


@pytest.mark.skipif(os.name != "nt", reason="the acceptance artifact is a Windows executable")
def test_release_executable_is_a_valid_pe_artifact() -> None:
    """Validate the release launcher without opening a GUI or live Codex."""

    if not RELEASE_EXECUTABLE.is_file():
        pytest.fail(f"release executable is missing: {RELEASE_EXECUTABLE}")

    data = RELEASE_EXECUTABLE.read_bytes()
    assert data[:2] == b"MZ"
    pe_offset = int.from_bytes(data[0x3C:0x40], byteorder="little")
    assert data[pe_offset : pe_offset + 4] == b"PE\0\0"


@pytest.mark.skipif(os.name != "nt", reason="the acceptance artifact is a Windows executable")
def test_built_sidecar_handshake_health_status_and_clean_termination(tmp_path: Path) -> None:
    if not SIDECAR.is_file():
        pytest.fail(f"built sidecar is missing: {SIDECAR}")

    token = "packaged-contract-token"
    process = subprocess.Popen(
        [
            str(SIDECAR),
            "--host",
            "127.0.0.1",
            "--port",
            "0",
            "--db-path",
            str(tmp_path / "contract.sqlite3"),
            "--token",
            token,
            "--log-dir",
            str(tmp_path / "logs"),
        ],
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()
    reader = threading.Thread(target=_read_lines, args=(process.stdout, lines), daemon=True)
    reader.start()
    try:
        readiness = json.loads(lines.get(timeout=15))
        assert readiness["event"] == "ready"
        port = int(readiness["port"])
        base_url = f"http://127.0.0.1:{port}"
        assert _get_json(f"{base_url}/healthz") == {"status": "ok"}
        status = _get_json(f"{base_url}/api/system/status", token)
        assert status["service"] == "ok"
        assert status["database"] == "reachable"
    finally:
        process.terminate()
        process.wait(timeout=10)
        assert process.returncode is not None
