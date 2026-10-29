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

### SMOKE-WIN-003 diagnosis and remediation

The packaged backend route was healthy. In an isolated run of the generated
sidecar, the canonical request returned:

```text
HTTP 201
Content-Type: application/json
Body: {"workflow":{"id":"test1","name":"Quick Smoke Test","description":null,"tasks":[],"edges":[]}}
```

The root cause was in the packaged frontend runtime wiring: `DesktopStartupGate`
loaded the sidecar `baseUrl` and bearer token but discarded the result. Default
API clients therefore sent a relative `/api/workflows` request without the
sidecar URL or authorization header. The HTTP client also attempted JSON
parsing before checking the HTTP status, so a non-JSON response from the wrong
origin was reported only as `response was not valid JSON`.

The repair injects the loaded desktop runtime into default requests and maps
non-JSON HTTP failures to a useful `HTTP_ERROR` while preserving the existing
invalid-success-response behavior.

Files changed:

- `frontend/src/api/http.ts`
- `frontend/src/api/client.test.ts`
- `frontend/src/api/http.desktop.test.ts`

Regression and packaged validation:

- Frontend focused tests: 14 passed.
- Backend API/workflow tests: 5 passed.
- Frontend typecheck, lint, and production build: passed.
- Ruff: passed.
- A fresh packaged sidecar probe created a unique disposable workflow and then
  retrieved it successfully: POST 201, GET 200, JSON content type, no backend
  traceback.
- Final NSIS rebuild: passed.

Final NSIS artifact:

| Artifact | Absolute path | Size (bytes) | SHA256 | Last write |
| --- | --- | ---: | --- | --- |
| NSIS installer | `D:\fiona\Codex_Projects\Task_Arrangements\desktop\src-tauri\target\release\bundle\nsis\Codex Flow_0.1.0_x64-setup.exe` | 17960171 | `6144B052365C16CA40CF7AB12215F90CBEDEFE45DA8F1606088F9F6426E001D0` | `2026-10-29T20:56:02.2231457+08:00` |
| Release executable | `D:\fiona\Codex_Projects\Task_Arrangements\desktop\src-tauri\target\release\codex-flow-desktop.exe` | 9091584 | `F75571993AD43B27FDF640144B38CDCBC9161118A4AAD63755AF04D680381237` | `2026-10-29T20:56:02.2530220+08:00` |

Automated remediation is **PASS**. The original manual result remains **FAIL**;
manual retest is **PENDING**.

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

The first post-fix automated desktop launch probe was blocked on this host.
The baseline launch and a launch with the existing profile failed during Tauri
WebView creation with:

`WebView2 error: WindowsError(Error { code: HRESULT(0x800700AA), message: "requested resource is in use" })`

The debug build reported the same error before the application could create
its window. No Codex Flow, sidecar, or WebView2 process was running before the
baseline launch, and no WebView2 environment override or relevant policy
registry value was present. The installed WebView2 Runtime was
`156.0.4314.50` at `C:\Program Files (x86)\Microsoft\EdgeWebView\Application`.

The official diagnostic `WEBVIEW2_USER_DATA_FOLDER` isolation launch used a
new temporary directory and remained alive. Its WebView2 profile was created
under that directory. This identifies the failure as a default Codex Flow
WebView profile resource conflict, not a missing runtime, host-wide WebView2
failure, or sidecar defect.

The smallest product-safe repair sets a stable process-local
`WEBVIEW2_USER_DATA_FOLDER` before Tauri creates the window, only when the user
has not already supplied one. The stable application-owned path is
`%LOCALAPPDATA%\com.codexflow.desktop\CodexFlowWebView2`; it is not temporary,
random, persisted as an environment override, or shared with another app.

After the repair, a clean rebuilt release executable remained alive for eight
seconds, and the sidecar and WebView2 processes were present. The rebuilt
artifacts are:

| Artifact | Size (bytes) | SHA256 |
| --- | ---: | --- |
| `desktop/src-tauri/target/release/codex-flow-desktop.exe` | 9091584 | `48C57185391E0793415E25EC2BAF7725FC8865D4968A6E320356CC2FC0353273` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 17959739 | `26A4999C0FD580D1F866AC0988F156BEAC222AD79F1545F223E0EBC0E9C2B7FA` |

Automated post-fix launch is **PASS**. Manual retest remains **PENDING**.

## SMOKE-WIN-003

Step: Create a new workflow in the installed Codex Flow application.

Input:

- Workflow id: `test1`
- Name: `Quick Smoke Test`

Expected: Workflow is created and the application transitions to the
workflow/editor or success state.

Observed: The UI displays `response was not valid JSON`; the workflow is not
created.

Result: **FAIL**

Status: **UNDER INVESTIGATION**
