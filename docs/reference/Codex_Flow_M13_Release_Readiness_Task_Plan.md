# Codex Flow — M13 V1 Release Readiness Task Plan

## Goal

Produce repeatable, evidence-backed V1 release readiness for the real installed
Windows Tauri/WebView2 application at the current source revision. M13 closes
the gap between the completed M0–M12 implementation work and a current,
verified installed-desktop acceptance result.

## Non-goals

- No scheduler, persistence-authority, or CodexAdapter architecture change.
- No cloud, multi-user, supervisor, model-routing, payment, or V2 work.
- No use of private Codex Desktop state as product authority.
- No GitHub Release publication without separate authorization.

## Execution order

`M13-01 → M13-02 → M13-03 → M13-04 → M13-05 → M13-06`

Every task uses the checkpoint, validation, completion commit, and push
protocol from `AGENTS.md` and `.codex/AUTO_EXECUTION.md`.

## M13-01 — Project Baseline & Progress Reconciliation

**Dependencies:** M12-REPORT-038  
**Owned Files:** `.codex/progress.json`, `docs/current-progress.md`,
`docs/reference/Codex_Flow_M13_Release_Readiness_Task_Plan.md`,
`docs/reference/Codex_Flow_Master_Roadmap.md`, `docs/v1-acceptance.md`

**Implementation:** Record M13 without rewriting M0–M12 history; distinguish
historical validation from evidence required for the current source/installer;
register the six-task dependency order and record pre-existing M13-03 E2E
working-tree changes as preserved, uncommitted work.

**Acceptance / Required Tests:** Git baseline, progress metadata, plan/task
order, roadmap, and V1 acceptance wording agree. No tracked user work is
discarded or overwritten.

**Completion Gate:** `next_task` is `M13-02`; M13-01 has a durable completion
record and pushed evidence.

## M13-02 — Windows Build & Install Reliability

**Dependencies:** M13-01  
**Owned Files:** `scripts/build_desktop.ps1`, `scripts/**build*`,
`desktop/tests/build_idempotency.md`, `docs/windows-build-artifacts.md`,
`docs/current-progress.md`, `.codex/progress.json`

**Implementation:** Diagnose the exclusive TEMP build lock without deleting or
bypassing it; record any holder only when it is demonstrably a Codex Flow
build. Use `scripts/build_desktop.ps1 -BundleTarget nsis`; validate frontend,
sidecar, bundled Codex CLI, Tauri, NSIS, marker-aware payload identity; install
the new package while preserving user data; verify installed EXE equals the
extracted NSIS payload.

**Acceptance / Required Tests:** Build-lock diagnostic, formal build script,
NSIS payload gate, installed identity SHA256 comparison.

**Completion Gate:** A current NSIS package and matching installed payload are
recorded with SHA256 evidence.

## M13-03 — Desktop E2E Infrastructure

**Dependencies:** M13-02  
**Owned Files:** `scripts/desktop_e2e_v1.mjs`,
`scripts/run_desktop_e2e_v1.ps1`, `scripts/**desktop*e2e*`,
`docs/v1-acceptance-evidence.md`, `docs/current-progress.md`,
`.codex/progress.json`

**Implementation:** Stabilize the existing real installed-app CDP runner:
loopback-only dynamic CDP port, bounded timeouts, unique workflow/run IDs,
isolated test workspaces, safe owned-process cleanup, JSON reports, REST/
SQLite/Event Log/filesystem/process evidence, and token-safe diagnostics.
Normal production startup must not expose CDP.

**Acceptance / Required Tests:** The runner attaches only to the installed
Codex Flow WebView2 target and emits a machine-readable report; failure reports
retain a safe phase and owned-process cleanup occurs.

**Completion Gate:** A stable runner is ready for full functional regression.

## M13-04 — Full V1 Functional Regression

**Dependencies:** M13-03  
**Owned Files:** existing Desktop E2E scripts/tests and
`docs/v1-acceptance-evidence.md`, plus directly implicated bounded remediations.

**Implementation:** Exercise installed UI CRUD, graph dragging/persistence,
real A→B→C Codex DAG output verification, runtime states and stale-WebSocket
recovery, Run Detail/task controls, deterministic failure/retry/recovery,
duplicate/race protection, Open in Codex evidence or `AUTOMATION_LIMITATION`,
and shutdown/reopen persistence.

**Acceptance / Required Tests:** UI action → API → SQLite → UI evidence for
each automatable item; no old artifact, mock Codex completion, or fabricated
state is accepted.

**Completion Gate:** Full installed regression passes or every remaining
manual-only limitation is explicitly documented without masking a defect.

## M13-05 — Final Installed Acceptance

**Dependencies:** M13-04  
**Owned Files:** E2E scripts/tests, build evidence, acceptance evidence,
`docs/current-progress.md`, `.codex/progress.json`

**Implementation:** Run frontend, backend, and Tauri regressions; rebuild and
install the formal NSIS package; verify identity and execute the full installed
E2E cycle three consecutive times. Any implementation fix resets the cycle
count after rebuild/reinstall.

**Acceptance / Required Tests:** all declared non-live regressions pass and
installed E2E is 3/3 consecutive PASS.

**Completion Gate:** release candidate evidence is current and reproducible.

## M13-06 — Release Readiness & Evidence

**Dependencies:** M13-05  
**Owned Files:** `README.md`, `CHANGELOG.md`, `docs/current-progress.md`,
`docs/manual-v1-checklist.md`, `docs/v1-acceptance-evidence.md`,
`docs/reference/*M13*`, `.codex/progress.json`

**Implementation:** Publish repository-local release notes and final M13
report; record source commit, NSIS/payload/installed hashes, test results,
manual-only items, known limits, and historical failures. Do not publish a
GitHub Release or start M14.

**Acceptance / Required Tests:** evidence accurately matches the current
implementation and has no false PASS claims.

**Completion Gate:** M13 is COMPLETE, `active_task` and `next_task` are null,
and V1 release readiness is explicitly READY or NOT READY.
