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
