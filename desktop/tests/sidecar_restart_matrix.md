# Desktop Sidecar Restart Matrix

This bounded Rust matrix exercises eight deterministic Fake-mode sidecar
start/crash/relaunch cycles against the same app-data database path.

Each cycle verifies:

- the child exit is observable before relaunch;
- one relaunch is allowed and receives a fresh session identity;
- the database path remains the same across the restart;
- a second relaunch is rejected, preventing a relaunch loop;
- every launch identity is unique, so a restart cannot reuse one external
  execution identity or create a duplicate prompt for the same Attempt.

Run from the repository root on Windows:

```powershell
cargo test --manifest-path desktop/src-tauri/Cargo.toml repeated_fake_restart_cycles_reuse_app_data_without_duplicate_identity
```

The test uses `cmd.exe` as the deterministic Fake sidecar process. It does
not contact Codex or execute a live workflow; scheduler Attempt/prompt
deduplication remains covered by the backend Fake adapter stress matrix.
