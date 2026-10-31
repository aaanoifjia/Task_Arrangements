# Codex Flow

Codex Flow is a local desktop product for orchestrating Codex tasks as a
deterministic directed acyclic graph (DAG). It keeps workflow definitions,
runs, attempts, controls, recovery state, and event history in a local SQLite
database. The desktop shell hosts the local backend sidecar and the frontend
workflow editor/run history UI.

The automated M12 productization gate is complete. Installer launch, native
Desktop behavior, real Codex execution, and subjective UI review remain in the
user-owned [manual V1 checklist](docs/manual-v1-checklist.md).

## Product boundaries

- Workflow dependencies and progression are deterministic and fail closed.
- Codex execution remains behind the adapter boundary; automated validation
  uses the repository Fake adapter and does not require live Codex credentials.
- The desktop runtime uses local app-data paths and a local SQLite store.
- Manual controls, retry attempts, continuation threads, event history, and
  diagnostics are durable and redacted for user-facing status surfaces.

## Backend setup

Requirements:

- Windows
- Python 3.11+

Create the virtual environment:

```powershell
py -3.11 -m venv .venv
```

Install the backend in editable mode:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "backend[dev]"
```

Verify the package:

```powershell
.\.venv\Scripts\python.exe -c "import codex_flow; print(codex_flow.__version__)"
```

## Frontend and desktop development

Install the already-declared frontend dependencies, then run the local UI:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

For the Tauri desktop shell, use the existing per-user Rust toolchain and the
repository's desktop scripts. The full bundle pipeline remains the default;
the explicit NSIS mode is available for local idempotency checks when the host
Windows Installer service is unavailable:

```powershell
$env:Path = "C:\Users\Administrator\.cargo\bin;$env:Path"
.\scripts\build_desktop.ps1
.\scripts\build_desktop.ps1 -BundleTarget nsis
```

See [the productization test report](docs/productization-test-report.md) for
the exact automated evidence and [the manual checklist](docs/manual-v1-checklist.md)
for the remaining release-candidate observations.

### Installed Windows Desktop diagnostics

The installed Tauri/WebView2 application can be inspected without a mouse or
keyboard by enabling a loopback-only CDP port for the debug process:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/debug_windows_desktop.ps1 -CloseExisting -KeepOpen
node scripts/webview2_cdp_probe.mjs --port <port> --text 'Start run'
```

The helper launches only the installed Codex Flow process tree, uses a
repo-local temporary directory for PyInstaller extraction, and restores the
parent process environment when it exits. Remote debugging is not enabled by
normal production startup.
