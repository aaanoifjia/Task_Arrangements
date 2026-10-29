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
