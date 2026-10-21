# M9 Desktop Packaging Test Report

Updated: 2026-10-22

## Automated result

The automated M9 gate is **PASS**. The checks below were run without reading or
modifying private Codex Desktop databases, LevelDB, renderer IPC, or other
private Desktop state.

| Area | Result | Evidence |
| --- | --- | --- |
| Frontend regression | PASS | `npm --prefix frontend run test:run`: 52 files, 173 tests; typecheck, ESLint, and production build passed |
| Backend non-live regression | PASS | `\.venv\Scripts\python.exe -m pytest backend/tests -m "not live_codex"`: 257 passed, 6 deselected |
| Sidecar build and staging | PASS | PyInstaller sidecar build completed; target-named executable and `_internal` runtime staged for Tauri |
| Tauri release executable | PASS | `codex-flow-desktop.exe` built by the authoritative `scripts/build_desktop.ps1` flow |
| Windows MSI bundle | PASS | `Codex Flow_0.1.0_x64_en-US.msi`; 8,585,216 bytes; SHA256 `DE244EEBFCC22E5550F7DEED77727495F594C715F122EB6420F070A2A5565D23` |
| Windows NSIS bundle | PASS | `Codex Flow_0.1.0_x64-setup.exe`; 7,603,613 bytes; SHA256 `BA8B315FBFF0302274CDDC1FB2B96B0B038C0413724D33332EA4EEC32141A46C` |
| Rust/Tauri tests | PASS | `cargo test --manifest-path desktop/src-tauri/Cargo.toml`: 25 passed; `cargo check` passed |
| Startup/shutdown and crash/relaunch | PASS | M9 desktop integration harness and Tauri sidecar lifecycle tests passed, including clean termination, unexpected exit, bounded relaunch, and no-loop behavior |
| App-data DB and log paths | PASS | Tauri path/runtime tests prove normalized per-user app-data SQLite/log paths and reuse across launches; install-directory storage is not used |
| Codex authentication home | PASS | Tauri environment-construction tests prove canonical `HOME`/`USERPROFILE` inheritance and no auth redirection to app-data |
| Token security | PASS | Auth middleware, token-safe health/handshake, redaction, runtime-state, frontend bridge, and implementation-path secret scans passed |
| Native notification bridge | PASS | Desktop notification adapter tests 2/2 and browser notification/deduplication tests 4/4 passed |
| Open-in-Codex bridge | PASS | Strict `codex://threads/<id>` validation and native bridge invocation tests 3/3 passed; Tauri integration suite passed |
| Security/path constraints | PASS | No credential-like literals, private Codex Desktop state access, or hard-coded desktop backend port in production implementation paths |

The exact bundle manifest is maintained in
[`docs/windows-build-artifacts.md`](windows-build-artifacts.md).

## Deferred manual checks

The following are intentionally not claimed by this automated report:

- launching the MSI or NSIS installer through the Windows GUI;
- visual application UX, native notification appearance, and window behavior;
- opening a real `codex://threads/<id>` URI in Codex Desktop;
- confirming Desktop sidebar/search visibility and project association;
- observing whether any Desktop action requires a manual Enter key.

These checks remain part of the final manual V1 gate after M10 automated
hardening completes.
