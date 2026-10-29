# Codex Flow V1 Manual Smoke Test Report

Test round: 1  
Platform: Windows 10 x64  
Artifact: `Codex Flow_0.1.0_x64-setup.exe`  
Artifact SHA256: `D220D3EA9DBFA3336D0272D98100A7803BB7810B3519F108571E4378E543B008`

## Round 1 — SMOKE-WIN-001

Step: Launch the installed Codex Flow desktop application.

Expected: The application window remains open, the packaged sidecar reaches
readiness, and the normal UI becomes usable.

Observed: The installed Codex Flow application opens and immediately
exits/crashes before the normal UI becomes usable.

Result: **FAIL**

Status: **UNDER INVESTIGATION**

The original failure is preserved as the baseline and must not be replaced by
post-fix evidence. The remaining manual checklist is not marked PASS by this
report.

## Root cause

The Tauri installer copied the PyInstaller onedir launcher as
`codex-flow-server.exe` but did not copy its sibling `_internal` runtime
directory. The packaged launcher therefore failed before readiness with:

`Failed to load Python DLL ...\_internal\python311.dll`

The desktop process waited for sidecar readiness and exited with code `101`.
The independent staged sidecar, including its `_internal` directory, reached
readiness successfully.

## Remediation status

The sidecar packaging path is being changed to a single-file PyInstaller
artifact so the existing Tauri external-binary contract carries the complete
runtime. Automated post-fix launch evidence and a rebuilt installer will be
recorded below after validation. Manual retest remains **PENDING**.

## Post-fix automated evidence

The single-file sidecar passed `--version`, emitted readiness, and returned
`200 {"status":"ok"}` from `/healthz` in an isolated controlled run.

The rebuilt NSIS artifacts are:

| Artifact | Size (bytes) | SHA256 |
| --- | ---: | --- |
| `desktop/src-tauri/target/release/codex-flow-desktop.exe` | 9096192 | `806534BB9BCCD5C7DD9CA7F89384B3FE37B0EF5424E53F19EF0A14E3985C4A45` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 17956685 | `C4AE247EB3F9900FFBC35445045E6F64465BB7865511D33E749B4B4224B9FF1F` |

The automated desktop launch probe remains **BLOCKED** on this host. Both a
normal launch and a launch with a fresh temporary profile fail during Tauri
WebView creation with:

`WebView2 error: WindowsError(Error { code: HRESULT(0x800700AA), message: "requested resource is in use" })`

The debug build reports the same error, before the application can create its
window. This is a host WebView2 resource-lock prerequisite, separate from the
fixed sidecar packaging defect. Manual retest remains **PENDING**.
