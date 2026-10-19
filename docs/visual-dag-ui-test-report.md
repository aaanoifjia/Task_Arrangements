# Codex Flow M7 Visual DAG UI Milestone Report

Date: 2026-10-20  
Result: PASS

## Evidence

The M7 frontend acceptance matrix passed with 45 test files and 111 tests. The integrated mocked user flow passed independently, covering workflow discovery, creation, multi-node editing, validation, save/reload, run launch, live snapshot/event delivery, task inspection, attempt history, Open-in-Codex URI generation, and terminal summary. TypeScript type checking, ESLint, and the production Vite build also passed.

The complete non-live backend regression passed 141 tests; 6 live Codex tests were intentionally excluded from this local UI gate. The M6 and M5 durable API/runtime contracts therefore remained green without invoking live credentials.

| Result | Gate | Evidence |
| --- | --- | --- |
| PASS | Frontend bootstrap | Vite/React application mounted through the app router and the full frontend suite passed. |
| PASS | Workflow list, create, edit, and save | `WorkflowListPage`, `NewWorkflowForm`, editor page/layout, save button, API mocks, and integration flow passed. |
| PASS | Multi-task nodes | Editor matrix and integration flow exercised a two-node DAG and task selection/editing. |
| PASS | Complete Prompt | Task inspector prompt editing and serialized workflow update were exercised by editor and integration tests. |
| PASS | CWD/config fields | Task inspector field tests cover working directory, sandbox, model, reasoning, approval, timeout, retry, and continuation configuration. |
| PASS | Dependency edge editing | Canvas/editor matrix covers connect and disconnect operations and serialized edges. |
| PASS | Cycle prevention | Editor validation tests reject cyclic graphs and keep Save disabled for invalid graphs. |
| PASS | Run launch | Start-run tests and the integration flow verify saved/valid gating, POST mapping, and run navigation. |
| PASS | Run history | Run list/filter and workflow-to-run navigation tests passed. |
| PASS | Run DAG statuses | Read-only React Flow snapshot rendering and canonical status mapping tests passed for mixed states. |
| PASS | WebSocket updates | Snapshot/event application, cursor reconnect, duplicate suppression, terminal cleanup, and integration-flow streaming tests passed. |
| PASS | Event log | Durable event ordering, references, cursor data, and compact payload rendering tests passed. |
| PASS | Attempt history | Lazy attempt loading and API-order rendering passed in drawer and integration tests. |
| PASS | Failure/needs-attention presentation | Deterministic FAILED, INTERRUPTED, BLOCKED, and NEEDS_ATTENTION notices passed without unsupported controls. |
| PASS | Open-in-Codex URI contract | Exact encoded `codex://threads/{thread_id}` URI and missing-thread behavior passed. |
| PASS | M6/M5 regression | `\.venv\Scripts\python.exe -m pytest backend/tests -m "not live_codex"`: 141 passed, 6 deselected. |
| PASS | No master LLM control | The UI consumes durable API/WebSocket data and does not decide dependencies, retries, readiness, or workflow progression. |

## Exact validation commands

```text
frontend\> npm run test:run
45 files passed; 111 tests passed

frontend\> npm run typecheck
PASS

frontend\> npm run lint
PASS

frontend\> npm run build
PASS — Vite transformed 261 modules and produced the production bundle

repo\> \.venv\Scripts\python.exe -m pytest backend/tests -m "not live_codex"
141 passed, 6 deselected
```

## Manual verification boundary

Automated coverage verifies the exact Open-in-Codex URI contract. Opening the URI in Codex Desktop, confirming sidebar/search behavior, and other desktop observations remain deferred to the M9 manual UX gate; no private Desktop state was accessed.

## Gate decision

PASS — the frozen M7 Visual DAG UI milestone is complete. No authoritative M8 task plan is present, so `next_task` remains null.
