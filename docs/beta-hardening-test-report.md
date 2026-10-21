# Codex Flow M10 Beta Hardening Test Report

Updated: 2026-10-22

## Result

PASS for the automated M10 beta gate. No live Codex execution was run during
the final gate. Manual Desktop/UI checks remain explicitly pending and are
listed in [`manual-v1-checklist.md`](manual-v1-checklist.md).

## Exact automated evidence

| Area | Command | Result |
|---|---|---|
| Backend regression | `\.venv\Scripts\python.exe -m pytest backend/tests -q -m "not live_codex"` | `348 passed, 6 deselected, 2 xfailed, 7 warnings` |
| Packaging and stress suite | `\.venv\Scripts\python.exe -m pytest backend/tests/packaging backend/tests/stress -q -m "not live_codex"` | `22 passed, 1 warning` |
| Frontend tests | `npm run test:run` from `frontend/` | `52 test files, 177 tests passed` |
| Frontend type safety | `npm run typecheck` from `frontend/` | PASS |
| Frontend lint | `npm run lint` from `frontend/` | PASS |
| Frontend production bundle | `npm run build` from `frontend/` | PASS; Vite production assets emitted |
| Tauri compile | `cargo check --manifest-path desktop/src-tauri/Cargo.toml` | PASS |
| Tauri Rust tests | `cargo test --manifest-path desktop/src-tauri/Cargo.toml` | `26 passed, 0 failed` |

The backend suite includes the scheduler, adapter, state-machine, readiness,
lock, continuation, retry, timeout, recovery, crash, event-volume, API,
packaging, and stress coverage accumulated through M10. The final gate did not
run the six live Codex tests.

## Hardening coverage recorded before the gate

- deterministic duplicate-prevention matrix: 7 passed;
- degraded frontend recovery matrix: 18 passed;
- desktop sidecar restart soak: 8 deterministic cycles and 26/26 Tauri tests;
- accelerated Fake workflow soak: 24 iterations with mixed success/tool-failure
  outcomes and no leaked runtime tasks;
- frontend reconnect soak: 100 cursor-resumed reconnects with event dedupe;
- v1 acceptance evidence: all 22 items mapped in
  [`v1-acceptance-evidence.md`](v1-acceptance-evidence.md).

## Manual boundary

Automated checks do not claim successful installer launch, native notification
appearance, actual Open-in-Codex Desktop behavior, sidebar/search visibility,
or the absence of a manual Enter between tasks. Those observations require the
final checklist and user interaction.
