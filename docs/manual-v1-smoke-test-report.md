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

## Workflow persistence manual verification

The user manually created and re-opened the persisted workflow through the
installed Codex Flow GUI. The workflow definition persisted with the expected
two-task DAG (`Task A → Task B`).

Result: **PASS**

## SMOKE-WIN-005 — Live task remains stuck in STARTING

Step: Run the persisted two-task workflow from the installed Codex Flow GUI.

Expected: Task A transitions `STARTING → RUNNING` and begins a real Codex
execution; after its success, Task B becomes ready and starts automatically.

Observed: The user clicked Run in the installed GUI. Task A remained in
`STARTING` for several minutes, Task B did not start, and the user did not
retry, cancel, pause, restart, or interact with Codex Desktop.

Result: **FAIL**

Status: **UNDER INVESTIGATION**

### Preserved live-run evidence

Read-only inspection of workflow run
`1c9f7277-bebd-4343-be4c-8f394971de97` found:

- workflow run: `RUNNING`;
- Task A task run and its sole attempt: `STARTING`;
- Task B: `BLOCKED`;
- Task A/attempt `thread_id` and `turn_id`: absent;
- durable event sequence: empty.

The final successful durable boundary was the transactional persistence of the
STARTING attempt at `2026-10-30T08:12:10.446149+00:00`. No adapter/thread,
turn, or stream event was recorded. The installed sidecar was alive but had no
Codex child process, so the blocked boundary was adapter startup before thread
creation.

### Root cause and remediation

The Windows user environment had `USERPROFILE`, `HOMEDRIVE`, and `HOMEPATH`,
but no `HOME`. The local Codex CLI failed to load its configuration without a
home directory. With `HOME` derived from the existing `USERPROFILE`, the
already-installed Codex CLI reported `Logged in using ChatGPT`; this proves an
environment-inheritance defect rather than an authentication gate.

The runner also allowed an exception from adapter startup to escape its
background task after it had persisted `STARTING`, leaving no terminal state.
The remediation derives only a missing `HOME` from existing Windows profile
variables for the SDK-owned subprocess and fail-closes a startup exception as
`FAILED`, including a credential-free `TASK_START_FAILED` audit event.

Automated remediation: **PASS** — focused regression, the relevant durable
runner regression, the non-live backend suite, Ruff, and strict mypy passed.
A freshly rebuilt NSIS installer was installed over the existing application.

### Follow-up live adapter evidence

The repaired SDK completed a real single-task file smoke using the existing
authenticated Windows Codex environment. A real durable two-task DAG then
reached `A=SUCCESS`, `B=SUCCESS` automatically, with distinct thread and turn
identifiers for both tasks and no manual continuation.

During that test, normal app-server informational notifications
(`turn/moderationMetadata` and `thread/tokenUsage/updated`) were found to be
incorrectly mapped as `TRANSPORT_ERROR`. That could turn a healthy Codex turn
into `FAILED`; it is now ignored rather than treated as transport evidence.

The live agent did not reliably honor the byte-exact/no-trailing-newline file
instruction: one run wrote both expected values with a trailing newline, and
one explicit-command run reported a completed turn without creating the
requested file. These external-output observations are preserved. They do not
justify inferring filesystem success from agent prose or redesigning the
frozen scheduler; the packaged installed-app retest must verify the real
outputs before SMOKE-WIN-005 can be marked manually passed.

### Packaged recovery and retest artifact

After the repaired NSIS installer was installed, the original preserved run
was inspected read-only. Startup recovery had deterministically changed Task A
from the previously orphaned `STARTING` state to `FAILED`; Task B remained
`BLOCKED`, with no thread or turn identifiers. This confirms that the original
failure can no longer remain indefinitely in `STARTING` after an application
restart. It is recovery evidence, not a replacement for a fresh manual GUI
run.

The installed desktop and two sidecar processes were live and responding. The
native accessibility bridge exposed no rendered content and its screenshot
request timed out in this environment, so a new GUI-driven run and its output
files could not be independently observed by automation in this pass.

Fresh retest artifact:

| Artifact | Absolute path | Size (bytes) | SHA256 | Last write |
| --- | --- | ---: | --- | --- |
| NSIS installer | `D:\\fiona\\Codex_Projects\\Task_Arrangements\\desktop\\src-tauri\\target\\release\\bundle\\nsis\\Codex Flow_0.1.0_x64-setup.exe` | 17963292 | `3565F99AD7007E1A65A8D92E83376388398823511487317237ECE7516D62DCF5` | `2026-10-30T16:40:32.2231074+08:00` |
| Release executable | `D:\\fiona\\Codex_Projects\\Task_Arrangements\\desktop\\src-tauri\\target\\release\\codex-flow-desktop.exe` | 9107968 | `5C01879B65E05853245F463438FCC567F0EAEDE6F0543DFA714EE58CF986FBE2` | `2026-10-30T16:40:32.2530542+08:00` |

The original manual result remains **FAIL** and the fresh manual GUI/output
retest remains **PENDING**. The environment has a usable authenticated Codex
session; this is not an authentication-only gate. The unresolved strict
criterion is visible live-agent output adherence plus GUI observation, which
must not be fabricated from terminal completion events.

### SMOKE-WIN-007 — Installed WebView navigation observation

Status: **UNCONFIRMED / DIAGNOSING**. The automation bridge reported
`about:blank`, but this is not yet evidence that the installed application is
blank. No `SMOKE-WIN-007` failure is recorded.

The latest source release was independently checked before any new rebuild:

- configured `frontendDist`: `../../frontend/dist`;
- `frontend/dist/index.html` exists and references
  `assets/index-StAksiA8.js` and `assets/index-BjHm3EnW.css`;
- both referenced assets exist;
- Tauri release dependency metadata lists those exact files and generated
  `tauri-codegen-assets`, proving that the release executable embeds the
  configured frontend resource set.

The installed executable launched from the normal per-user installation path
was also fingerprinted. It does **not** match the latest rebuilt release:

| Artifact | Absolute path | Size (bytes) | SHA256 | Last write |
| --- | --- | ---: | --- | --- |
| Installed executable | `C:\\Users\\Administrator\\AppData\\Local\\Codex Flow\\codex-flow-desktop.exe` | 9107968 | `8D68CB90253C141334FFF09A42F330F950E9C7513C0201551F55C3E6748AF691` | `2026-10-30T16:40:20+08:00` |
| Latest release executable | `D:\\fiona\\Codex_Projects\\Task_Arrangements\\desktop\\src-tauri\\target\\release\\codex-flow-desktop.exe` | 9107968 | `B0DE2DE8107D3521829A47EC30B096FD11210AE7CB92CBEBD41D7C956E019E68` | `2026-10-30T19:08:13.8316890+08:00` |

Therefore the `about:blank` observation is currently attributable to an
unverified automation/install-selection mismatch, not a proven Tauri resource
or navigation failure. The next diagnostic step is to establish the exact
installed binary selected by Start Menu and capture WebView navigation/runtime
evidence from that matching build before changing frontend or Tauri
configuration.

### Stale-build recovery attempt

The old per-user executable was fingerprinted, the Codex Flow-owned processes
were closed, and the bundled uninstaller was run successfully. The uninstaller
left the mixed application/data directory in place, so only the confirmed old
application binaries and uninstaller were removed; the SQLite database, WAL,
SHM, and logs were preserved.

The required NSIS hash was verified before installation:

`43D2CA1F8C19306C318AB192ECA572DE23253864B1B1D2F18542948D8EBC31E7`

The elevated silent installation returned exit code 0, but the resulting
installed executable still did not match the corresponding release executable:

| Artifact | SHA256 |
| --- | --- |
| Required release EXE | `B0DE2DE8107D3521829A47EC30B096FD11210AE7CB92CBEBD41D7C956E019E68` |
| Installed EXE after exact NSIS install | `C64E485AD54BA877DF3BD8FE7ACBC69D57C17E84D4D5ECD15FE0EA839BBB45A1` |

Per the verification gate, the installed application was **not launched**.
This is now a confirmed packaging/install identity blocker; `SMOKE-WIN-007`
remains **NOT CONFIRMED** because no verified-current build was run and no
product UI conclusion can be drawn.

### Packaging identity investigation

The current NSIS was extracted to an isolated temporary destination without
launching Codex Flow. Its packaged executable measured:

`CBA35F913191D70BBBCD7B0C79572A50F3F7D64CC7D9CFAF1B04EC593E64E8C7`

The current release executable measured:

`045F5B6922BEC80520188D1C7A435FD2F47AA9C49DCBA36D1F0A0FBFE5B24695`

Both are unsigned and both report product/file version `0.1.0`; no intentional
signing or resource post-processing explains the difference. The NSIS payload
therefore differs from both the prior installed `C64E...` binary and the
current release binary: this is CASE C, an artifact staging/replacement
problem.

The Windows build script now holds an exclusive temporary build lock and, for
NSIS builds, extracts the generated installer to a disposable directory and
compares the payload SHA256 with the release executable. The identity gate
correctly fails on the current mismatch, preventing a stale installer from
being accepted for smoke testing. The clean rebuild remains blocked at this
gate; no application launch or further UI diagnosis was performed.

### HOME normalization follow-up

The implementation now explicitly rejects an environment with no usable home
information instead of silently passing a malformed environment. It preserves
an existing non-empty `HOME`, derives `HOME` from `USERPROFILE`, and falls
back to `HOMEDRIVE + HOMEPATH`; the existing `PATH`, `USERPROFILE`,
`HOMEDRIVE`, and `HOMEPATH` values remain inherited. The current interactive
Windows shell has `USERPROFILE`, `HOMEDRIVE`, `HOMEPATH`, and `PATH`, while
`HOME` is absent, matching the confirmed defect.

Environment regression: **6 passed**. Backend non-live regression, Ruff, and
strict mypy passed. The authenticated external Codex probe and the real
Codex Flow single-task and A→B probes passed previously with automatic Task B
readiness; output validation accepts the requested markers without requiring
byte-perfect newline behavior.

A fresh NSIS build and authorized silent installation completed. The installed
desktop and sidecar processes started, but the installed WebView exposed only
`about:blank` with no rendered application controls. Therefore the installed-app
live smoke is **FAIL / BLOCKED on the separate packaged UI load issue**; no
HOME error was observed. Manual retest remains **PENDING**.

Latest NSIS artifact:

| Artifact | Absolute path | Size (bytes) | SHA256 | Last write |
| --- | --- | ---: | --- | --- |
| NSIS installer | `D:\\fiona\\Codex_Projects\\Task_Arrangements\\desktop\\src-tauri\\target\\release\\bundle\\nsis\\Codex Flow_0.1.0_x64-setup.exe` | 17964626 | `43D2CA1F8C19306C318AB192ECA572DE23253864B1B1D2F18542948D8EBC31E7` | `2026-10-30T19:07:42.0558724+08:00` |
| Release executable | `D:\\fiona\\Codex_Projects\\Task_Arrangements\\desktop\\src-tauri\\target\\release\\codex-flow-desktop.exe` | 9107968 | `B0DE2DE8107D3521829A47EC30B096FD11210AE7CB92CBEBD41D7C956E019E68` | `2026-10-30T19:08:13.8316890+08:00` |

## SMOKE-WIN-004

Step: Open the installed Codex Flow application and access the Workflows page
or create a workflow.

Expected: The packaged frontend communicates with the localhost sidecar API and
loads workflow data.

Observed: The UI displays `Failed to fetch` on the initial page and when
creating a workflow.

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
