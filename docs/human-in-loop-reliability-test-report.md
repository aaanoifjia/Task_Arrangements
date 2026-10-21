# Codex Flow — M8 Human-in-the-Loop Reliability Report

Date: 2026-10-22  
Gate: `M8-GATE-043`  
Result: **PASS**

## Scope

M8 covers durable pause/resume, retry, cancel, skip, mark-success, failure and attention handling, audit events, race safety, the frontend control surface, the AttentionCenter, and the granted-only browser notification adapter. Scheduler progression remains deterministic and all controls remain behind the existing application/API boundaries.

## Automated evidence

| Gate | Command | Result |
| --- | --- | --- |
| Backend non-live regression and M8 control matrix | `\.venv\Scripts\python.exe -m pytest backend/tests --ignore=backend/tests/live --basetemp="C:\\Users\\Administrator\\.codex\\visualizations\\2026\\10\\18\\01a150b9-db73-7fb0-a24f-09371adf33f9\\m8-gate-pytest-final"` | **235 passed**, 1 non-blocking deprecation warning |
| Frontend Vitest regression | `npm --prefix frontend run test:run` | **49 test files, 160 tests passed** |
| Frontend type safety | `npm --prefix frontend run typecheck` | **PASS** (`tsc -b`) |
| Frontend lint | `npm --prefix frontend run lint` | **PASS** |
| Frontend production build | `npm --prefix frontend run build` | **PASS**; Vite transformed 267 modules |

The backend matrix includes control-contract validation, API error envelopes, pause/resume, retry identity and dependency release, queued/running cancellation, skip and mark-success legality, attention controls, audit persistence, terminal/control races, pause persistence/restart, WebSocket event cursors, scheduler readiness, locks, continuation, and failure propagation.

The frontend matrix includes control visibility, pending/error feedback, pause/resume refresh, explicit Retry, Cancel, Skip, Mark Success, keyboard confirmation and focus/Escape behavior, conflict refresh, AttentionCenter aggregation/navigation, notification permission states, M7 flow/accessibility regression, and the existing run/workflow views.

## Integration result

The Fake execution path is covered end-to-end for:

1. failed parent → blocked child;
2. explicit retry → parent success → child readiness;
3. durable pause → resume of ready work;
4. queued and running cancellation;
5. skip without dependent release;
6. mark-success with dependent release;
7. `NEEDS_ATTENTION` handling;
8. append-only control audit events and WebSocket delivery.

All automated paths passed without changing the frozen state-machine, DAG, adapter, or dependency architecture.

## Deferred manual limits

- Browser-native notification rendering was not manually verified. The adapter intentionally does not request permission; automated coverage verifies `granted`, `denied`, `default`, and TaskRun-id deduplication behavior.
- Codex Desktop/sidebar/deep-link visual checks remain deferred as required by the late-phase protocol.
- No credentials, live Codex execution, or native Windows packaging verification was required for the M8 automated gate.

## Advancement

M8 automated acceptance is complete. The deterministic next task is `M9-DESKTOP-001`.
