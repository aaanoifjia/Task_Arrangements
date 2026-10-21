# Codex Flow v1 Acceptance Evidence Matrix

Updated: 2026-10-22

This matrix maps every item in [`docs/v1-acceptance.md`](v1-acceptance.md)
to repository evidence. `PASS` means the named automated evidence exists and
passed. `PENDING` means the item still requires the final manual Desktop/UI
handoff; no manual result is inferred from file existence or automated tests.

| # | Acceptance item | Automated evidence | Manual evidence | Overall |
|---:|---|---|---|---|
| 1 | New Workflow | `frontend/src/features/workflows/NewWorkflowForm.test.tsx`, `backend/tests/api/test_workflow_routes.py` | Final browser workflow creation observation | PARTIAL — automated PASS; manual PENDING |
| 2 | Create multiple Task Nodes | `frontend/src/features/editor/EditorToolbar.test.tsx`, `frontend/src/features/editor/WorkflowCanvas.test.tsx` | Final browser multi-node observation | PARTIAL — automated PASS; manual PENDING |
| 3 | Node accepts a complete Prompt | `frontend/src/features/editor/fields/PromptField.test.tsx`, `frontend/src/features/editor/serialize.test.ts` | Final browser prompt-entry observation | PARTIAL — automated PASS; manual PENDING |
| 4 | Node sets Working Directory | `frontend/src/features/editor/fields/ExecutionFields.test.tsx` | Final browser working-directory observation | PARTIAL — automated PASS; manual PENDING |
| 5 | Drag edges to define Dependency | `frontend/src/features/editor/graphModel.test.ts`, `frontend/src/features/editor/WorkflowEditorMatrix.test.tsx`, `backend/tests/unit/test_graph.py` | Final browser edge-drawing observation | PARTIAL — automated PASS; manual PENDING |
| 6 | Save Workflow | `frontend/src/features/editor/SaveWorkflowButton.test.tsx`, `backend/tests/api/test_workflow_routes.py` | Final browser save/reload observation | PARTIAL — automated PASS; manual PENDING |
| 7 | Run Workflow | `frontend/src/features/runs/StartRunButton.test.tsx`, `frontend/src/integration/m7-flow.test.tsx`, `backend/tests/api/test_run_routes.py` | Final browser run-start observation | PARTIAL — automated PASS; manual PENDING |
| 8 | Scheduler automatically determines READY | `backend/tests/unit/test_readiness.py`, `backend/tests/unit/test_scheduler_matrix.py` | Not required | PASS |
| 9 | Create a Codex Thread only after READY | `backend/tests/unit/test_scheduler_matrix.py`, `backend/tests/integration/test_attempt_transaction.py`, `backend/tests/integration/test_retry_dependency_release.py` | Not required | PASS |
| 10 | Automatically send the complete Prompt | `backend/tests/unit/test_scheduler_core.py`, `backend/tests/integration/test_attempt_transaction.py`, `backend/tests/integration/test_runtime_manager.py` | Not required | PASS |
| 11 | Identify completed / failed / interrupt | `backend/tests/unit/test_tool_failure_mapping.py`, `backend/tests/integration/test_timeout_restart.py`, `backend/tests/integration/test_runtime_parity.py` | Not required | PASS |
| 12 | Predecessor failure blocks downstream | `backend/tests/integration/test_no_auto_retry_task_failure.py`, `backend/tests/stress/test_duplicate_prevention_matrix.py`, `backend/tests/integration/test_runtime_parity.py` | Not required | PASS |
| 13 | Predecessor success releases downstream | `backend/tests/unit/test_readiness.py`, `backend/tests/integration/test_retry_dependency_release.py`, `backend/tests/stress/test_duplicate_prevention_matrix.py` | Not required | PASS |
| 14 | Independent tasks run concurrently | `backend/tests/unit/test_locks.py`, `backend/tests/integration/test_multi_run_capacity.py`, `backend/tests/integration/test_persistent_fork_join.py` | Not required | PASS |
| 15 | Prevent dangerous same-workspace writes | `backend/tests/unit/test_locks.py`, `backend/tests/integration/test_persistent_workspace_serialization.py`, `backend/tests/integration/test_durable_workspace_lock.py` | Not required | PASS |
| 16 | Pause / Resume / Retry / Cancel | `backend/tests/integration/test_runtime_pause.py`, `backend/tests/integration/test_runtime_resume.py`, `backend/tests/integration/test_retry_dependency_release.py`, `backend/tests/integration/test_cancel_running.py`, `frontend/src/features/runs/RunControls.test.tsx` | Final manual control interaction | PARTIAL — automated PASS; manual PENDING |
| 17 | Recover after app restart | `backend/tests/integration/test_recovery.py`, `backend/tests/integration/test_timeout_restart.py`, `backend/tests/integration/test_continuation_recovery.py`, `backend/tests/stress/test_crash_fault_matrix.py` | Final manual restart observation | PARTIAL — automated PASS; manual PENDING |
| 18 | Run History | `frontend/src/features/runs/RunListPage.test.tsx`, `frontend/src/features/runs/navigation.test.tsx`, `backend/tests/api/test_run_routes.py` | Final browser history observation | PARTIAL — automated PASS; manual PENDING |
| 19 | Human attention notification | `frontend/src/features/attention/AttentionCenter.test.tsx`, `frontend/src/desktop/notifications.test.ts`, `backend/tests/integration/test_attention_controls.py` | Final native notification observation | PARTIAL — automated PASS; manual PENDING |
| 20 | Open the corresponding thread in Codex | `frontend/src/features/runs/OpenInCodex.test.tsx`, `desktop/src-tauri/src/open_external.rs` tests, M1 Desktop interoperability evidence | Actual Codex Desktop launch and target-thread observation | PENDING — final manual UX gate |
| 21 | No master LLM control | `backend/tests/unit/test_scheduler_matrix.py`, `backend/tests/unit/test_graph.py`, `backend/tests/integration/test_runtime_parity.py` | Not required | PASS |
| 22 | No manual Enter between tasks | Deterministic scheduler/runner terminal-event tests, including `backend/tests/stress/test_duplicate_prevention_matrix.py` | Direct observation during a real Desktop workflow | PENDING — final manual UX gate |

## Automated gate summary

The M10-HARDEN-033 regression passed with backend non-live `348 passed, 6
deselected, 2 xfailed`, frontend `52` test files / `177` tests plus
typecheck, ESLint, and production build, packaging contract `3 passed`, and
Tauri `cargo check` plus `26 passed` Rust tests. The M10-HARDEN-029 through
M10-HARDEN-032 stress matrices also passed.

The matrix deliberately leaves manual-only and both-mode UI observations
pending for the final manual handoff. This document does not claim that those
observations occurred.
