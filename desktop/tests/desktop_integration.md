# Desktop Integration Harness

This harness covers the desktop integration that can be verified without opening a
GUI window. It deliberately uses the existing Tauri sidecar/runtime contracts and
does not inspect Codex Desktop private state.

## Automated checks

Run from the repository root on Windows:

```powershell
cargo test --manifest-path desktop/src-tauri/Cargo.toml
npm --prefix frontend run test:run -- src/desktop/runtime.test.ts src/desktop/DesktopStartupGate.test.tsx
npm --prefix frontend run typecheck
npm --prefix frontend run lint
```

The Rust tests cover:

- loopback-only sidecar arguments and no shell invocation;
- canonical `HOME`, `USERPROFILE`, and `PATH` inheritance;
- app-data database/log paths and opaque bearer-token forwarding;
- readiness/runtime lifecycle state before and after a child exit;
- one bounded relaunch with a fresh token and no relaunch loop;
- idempotent shutdown of an already-exited child.

The frontend tests cover:

- browser mode remaining on relative defaults without a Tauri invoke;
- Tauri detection through the supported runtime markers;
- `runtime_state` invocation and preservation of the sidecar URL/token;
- startup loading, ready, failure, and retry-gate behavior without exposing
  backend failure details.

## Acceptance evidence

On 2026-10-22 the automated desktop integration checks passed with the existing
Tauri Rust suite, the focused frontend desktop suite, frontend typecheck, and
ESLint. GUI launch, sidebar visibility, and visual UX remain intentionally outside
this automated harness and are deferred to the final manual verification gate.
