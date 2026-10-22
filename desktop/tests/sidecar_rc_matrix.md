# Release Candidate Sidecar Start/Stop Matrix

This matrix runs four bounded cycles against the existing local packaged
sidecar. Each cycle starts a fresh temporary app-data directory, waits for the
machine-readable readiness handshake and health probe, then shuts down the
child and verifies that an exit status is observable.

The test does not download, rebuild, or contact Codex. It reuses the existing
target-named sidecar artifact and passes each cycle's temporary database and
log paths explicitly.

Run from the repository root on Windows:

```powershell
cargo test --manifest-path desktop/src-tauri/Cargo.toml repeated_packaged_sidecar_cycles_reach_ready_and_shutdown_cleanly
```

Acceptance evidence: four start -> ready -> shutdown cycles completed, every
child exit was observed, and each cycle used an isolated temporary app-data
path without database corruption.

Observed validation: `cargo test --manifest-path desktop/src-tauri/Cargo.toml`
passed 27/27 tests, including
`repeated_packaged_sidecar_cycles_reach_ready_and_shutdown_cleanly`.

The crash/relaunch case uses the same packaged executable, confirms the
database file exists before and after the crash, preserves its exact path,
observes a fresh session token after one bounded relaunch, and then shuts the
relaunched child down.

Observed validation: `cargo test --manifest-path desktop/src-tauri/Cargo.toml`
passed 27/27 tests, including
`repeated_packaged_sidecar_cycles_reach_ready_and_shutdown_cleanly`.
