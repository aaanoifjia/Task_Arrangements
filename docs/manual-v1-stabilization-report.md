# Codex Flow V1 Windows Stabilization Report

Status: **IN PROGRESS**

This report records the post-RC stabilization sprint without replacing the
historical evidence in [`manual-v1-smoke-test-report.md`](manual-v1-smoke-test-report.md)
or the user checklist in [`manual-v1-checklist.md`](manual-v1-checklist.md).

## Historical smoke failures

- [SMOKE-WIN-001](manual-v1-smoke-test-report.md#round-1--smoke-win-001): packaged startup crash. Startup remediation and manual retest are recorded as PASS.
- [SMOKE-WIN-002](manual-v1-smoke-test-report.md): closing the desktop left `codex-flow-server.exe`; remediation is pending in this sprint.
- [SMOKE-WIN-003](manual-v1-smoke-test-report.md#smoke-win-003): workflow creation returned invalid JSON. Automated repair commit `f32950c` is recorded; manual retest remains pending.
- [SMOKE-WIN-004](manual-v1-smoke-test-report.md#smoke-win-004): packaged frontend displayed `Failed to fetch`. This sprint is diagnosing the complete desktop boundary.

## Stabilization scope

The sprint covers the packaged Windows path end to end: WebView startup,
sidecar ownership and shutdown, runtime URL/token wiring, CORS/authenticated
workflow APIs, workflow-definition persistence, repeated launch cycles, and
the reusable release smoke harness.

Detailed evidence will be appended as each repair and validation gate passes.

## SMOKE-WIN-004 diagnosis

The installed desktop process reached a live WebView and exposed the actual
production origin as `http://tauri.localhost`. The owned sidecar was alive on a
loopback port and `/healthz` returned HTTP 200. The original browser-equivalent
preflight was:

```text
OPTIONS /api/workflows
Origin: http://tauri.localhost
Access-Control-Request-Method: GET
Access-Control-Request-Headers: authorization
HTTP 401
```

The backend log showed the sidecar startup but no workflow request. The token
middleware authenticated the preflight itself, so the browser stopped before
the actual GET/POST and surfaced `Failed to fetch`. The concrete repair lets
OPTIONS reach the existing explicit CORS allowlist while keeping bearer-token
authentication on all API data requests. No wildcard CORS or loopback binding
change was introduced.

## Stabilization repairs

- `081784e` — isolated WebView2 data directories per desktop process and
  terminated only the owned sidecar process tree during shutdown.
- `5a0e6dc` — allowed CORS preflight requests while retaining bearer auth for
  authenticated API requests.
- `f32950c` — injected packaged runtime URL/token into frontend API requests.

The reusable harness is [`scripts/smoke_windows_release.ps1`](../scripts/smoke_windows_release.ps1).
It exercises the packaged release executable, packaged sidecar, health check,
the exact `http://tauri.localhost` preflight, authenticated workflow list/create
and reload, two-task DAG persistence, and three consecutive isolated cycles.

## Automated stabilization gate

The final harness passed three consecutive cycles. Each cycle launched the
release executable, created the owned sidecar, verified the packaged
`http://tauri.localhost` CORS/auth boundary, round-tripped a unique two-task
workflow, and closed the desktop window through its native close message. The
owned sidecar process tree was gone after each graceful close; unrelated
processes were not targeted.

| Validation | Result |
| --- | --- |
| Backend non-live regression | 420 passed, 6 deselected, 2 xfailed |
| Backend packaging/stress | 25 passed |
| Ruff | PASS |
| Strict mypy | 56 source files, PASS |
| Frontend tests | 62 files, 216 tests passed |
| Frontend typecheck/lint/build | PASS |
| Tauri cargo check | PASS |
| Tauri cargo test | 32 passed |
| Packaged smoke harness | 3 consecutive cycles PASS |
| Live Codex execution | `LIVE-CODEX-MANUAL-GATE` — local Codex process exited with `Could not find home directory`; no credentials or account state were changed |

## Final NSIS artifact

| Artifact | Absolute path | Size (bytes) | SHA256 | Timestamp |
| --- | --- | ---: | --- | --- |
| NSIS installer | `D:\fiona\Codex_Projects\Task_Arrangements\desktop\src-tauri\target\release\bundle\nsis\Codex Flow_0.1.0_x64-setup.exe` | 17957648 | `C2B10DC5F2ACAE0D9C7CDD7F435936FDD075D46F64551D373655B62390568EB3` | `2026-10-29T22:35:43.1367560+08:00` |
| Release executable | `D:\fiona\Codex_Projects\Task_Arrangements\desktop\src-tauri\target\release\codex-flow-desktop.exe` | 9107968 | `4E2AEE753A5D8919317920C4A8CFA52F09AE5CE9EEAC6E993B029D0AD22E8CAD` | `2026-10-29T22:35:43.1683850+08:00` |

The artifact was installed through the supported silent NSIS path for local
validation. Manual retesting of the installed UI, native notifications,
Open-in-Codex, and subjective presentation remains user-owned.
