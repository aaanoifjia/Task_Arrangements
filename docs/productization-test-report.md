# Codex Flow — M12 Productization Test Report

Recorded: 2026-10-22  
Scope: offline/local M12 product-quality and operations validation

## Result

M12 automated acceptance PASS. M12-REPORT-038 records the release-candidate
evidence and hands the remaining installer, native Desktop, real-Codex, and
subjective UI checks to the user. The automated gate used the existing local
Python, Node/npm, Rust/Cargo, Tauri, PyInstaller, and repository dependencies.
It did not use live Codex execution, network access, new packages, new system
toolchains, credentials, or GUI interaction.

## M12 coverage

| Area | Evidence |
| --- | --- |
| Samples, onboarding, export/import | M12 sample, onboarding, export, and import task suites passed; deterministic sample materialization and replacement behavior remain covered. |
| Diagnostics and backup | Redacted diagnostics, safe diagnostic download, and explicit database-backup download/error behavior passed. |
| History and events | Cursor pagination, local history filters, event-type/task filters, stable ordering, duplicate suppression, and safe clipboard fallback passed. |
| Runtime/status UX | Redacted About/Runtime status, diagnostics navigation, startup retry bounds, and durable control-consequence guidance passed. |
| Accessibility | Keyboard-reachable primary actions, dialog focus restoration, labels, duplicate-id checks, and status/error roles passed. |
| Large UI fixtures | A 100-node editor DAG and 250-run/2,000-event history fixtures passed bounded mapping, validation, pagination, filtering, and duplicate-render checks. |

## Automated gate commands and results

All backend commands used `\.venv\Scripts\python.exe`.

| Area | Command/result |
| --- | --- |
| Backend non-live regression | `\.venv\Scripts\python.exe -m pytest backend/tests -q -m "not live_codex" --ignore=backend/tests/unit/test_workflow_export.py --basetemp backend/.pytest-tmp/m12-gate-037-backend` — **417 passed, 6 deselected, 2 xfailed** |
| Duplicate-name API export coverage | `\.venv\Scripts\python.exe -m pytest backend/tests/api/test_workflow_export.py -q --basetemp backend/.pytest-tmp/m12-report-api-export` — **2 passed** |
| Duplicate-name unit export coverage | `\.venv\Scripts\python.exe -m pytest backend/tests/unit/test_workflow_export.py -q --basetemp backend/.pytest-tmp/m12-report-unit-export` — **9 passed** |
| Packaging/stress | `\.venv\Scripts\python.exe -m pytest backend/tests/packaging backend/tests/stress -q -m "not live_codex" --basetemp backend/.pytest-tmp/m12-gate-037-packaging-stress` — **23 passed** |
| Ruff | `\.venv\Scripts\python.exe -m ruff check backend/src backend/tests` — **PASS** |
| Strict mypy | `\.venv\Scripts\python.exe -m mypy backend/src/codex_flow` — **56 source files, PASS** |
| Frontend tests | `npm --prefix frontend run test:run` — **61 files, 214 tests passed** |
| Frontend typecheck | `npm --prefix frontend run typecheck` — **PASS** |
| Frontend lint | `npm --prefix frontend run lint` — **PASS** |
| Frontend production build | `npm --prefix frontend run build` — **PASS** |
| Tauri compile | `$env:Path = "C:\Users\Administrator\.cargo\bin;$env:Path"; cargo check --manifest-path desktop/src-tauri/Cargo.toml` — **PASS** |
| Tauri Rust tests | `$env:Path = "C:\Users\Administrator\.cargo\bin;$env:Path"; cargo test --manifest-path desktop/src-tauri/Cargo.toml` — **31 passed, 0 failed** |

The backend collection command excludes only the duplicate-basename unit export
module so pytest can collect the remaining suite. Both excluded-by-collection
files were then run independently and passed (2 + 9 tests). The six live
Codex tests remain intentionally deselected by the `not live_codex` gate.

## M12 completion commits

The final M12 implementation and gate history is preserved in these commits:

- `07b951e` — M12-A11Y-034 accessibility regression
- `a4d1dae` — M12-A11Y-034-R1 bounded integration-test remediation
- `cde3c07` — M12-PERF-035 large DAG UI guard
- `702b4df` — M12-PERF-036 large history/event guard
- `49f6892` — M12-PERF-036-R1 full-suite test-harness remediation
- `ff76a67` — M12-GATE-037 productization automated gate

## Manual handoff

The automated evidence does not claim installer launch success, native
notification appearance, Open-in-Codex behavior, real Codex workflow execution,
or subjective UI quality. Those observations are preserved as unchecked items
in [`manual-v1-checklist.md`](manual-v1-checklist.md). Packaged artifact
evidence, including the existing successful M9 MSI/NSIS results and the M11
NSIS idempotency evidence, remains in
[`windows-build-artifacts.md`](windows-build-artifacts.md).

Manual verification is the remaining user-owned release-candidate handoff.
