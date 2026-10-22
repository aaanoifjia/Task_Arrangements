# Release Candidate App-data Path Harness

This harness exercises the desktop path lifecycle with a temporary user-data
root containing spaces and Unicode. Repeated preparation reuses one canonical
`Codex Flow` root, and the SQLite database, logs, and window-state file all
resolve below that root.

Run from the repository root on Windows:

```powershell
cargo test --manifest-path desktop/src-tauri/Cargo.toml lifecycle_keeps_all_writable_paths_inside_unicode_app_data_root
```

The test writes representative window-state and log files, verifies their
containment, and removes only its own temporary harness directory. No user
profile or external filesystem path is scanned.

Observed validation: `cargo test --manifest-path desktop/src-tauri/Cargo.toml`
passed 31/31 tests, including
`lifecycle_keeps_all_writable_paths_inside_unicode_app_data_root`.

Observed validation: `cargo test --manifest-path desktop/src-tauri/Cargo.toml`
passed 31/31 tests, including
`lifecycle_keeps_all_writable_paths_inside_unicode_app_data_root`.
