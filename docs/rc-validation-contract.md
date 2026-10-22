# Codex Flow — M11 Release Candidate Validation Contract

Updated: 2026-10-22

M11 is an offline, local release-candidate validation phase. Its checks may
inspect and execute tools that are already present in the repository
environment, but they must not install packages, download artifacts, contact
Codex services, perform external web research, or require Desktop/GUI
interaction.

## Declared prerequisites

The following prerequisites are required for the M11 validation sequence. The
status below is the result of the local preflight on 2026-10-22.

| Prerequisite | Status | Local evidence |
| --- | --- | --- |
| Project Python/virtual environment | PASS | `.venv/Scripts/python.exe` |
| PyInstaller | PASS | `.venv/Scripts/pyinstaller.exe` |
| Node.js | PASS | Existing `node` executable |
| npm | PASS | Existing `npm` executable |
| Rust compiler | PASS | Existing user-level Rustup `rustc` executable |
| Cargo | PASS | Existing user-level Rustup `cargo` executable |
| Git | PASS | Existing `git` executable |
| Tauri Cargo inputs | PASS | `desktop/src-tauri/Cargo.toml`, `build.rs`, `tauri.conf.json`, icons, and target-named sidecar |

`PASS` means the prerequisite is already available locally. `BLOCKED` is the
only permitted alternative status when a declared prerequisite is absent;
the preflight reports that state without attempting remediation.

## Explicit exclusions

M11 does not require live Codex execution, network access, new package
downloads, new third-party runtime dependencies, new system toolchains, or
manual GUI/Desktop verification. These exclusions are part of the release
candidate contract and keep the validation deterministic and offline.

## M11-GATE-035 automated evidence

Recorded on 2026-10-22. All checks used the existing local environment and
completed without network access, live Codex execution, credentials, or GUI
interaction:

| Area | Result |
| --- | --- |
| Backend non-live regression | `390 passed, 6 deselected, 2 xfailed` |
| Frontend Vitest | `52` files, `177` tests passed |
| Frontend typecheck/lint/build | PASS |
| Tauri cargo check | PASS |
| Tauri Rust tests | `31 passed, 0 failed` |
| Packaging and stress suite | `23 passed` |
| Packaged sidecar smoke | `2 passed`; readiness, healthz, authenticated system status, clean termination |
| Targeted regression after gate repairs | `10 passed` |
| Ruff | PASS for backend, desktop tests, and scripts |
| Strict mypy | PASS for `backend/src/codex_flow` (52 files) |
| Windows release build | Two NSIS-only idempotency runs passed; MSI/WiX was not rebuilt because the Windows Installer service remained unavailable |

The gate claims automated evidence only. Manual Desktop/UI checks remain
deferred to M12-REPORT-038.

## M11-GATE-035 automated evidence

Recorded on 2026-10-22. All checks used the existing local environment and
completed without network access, live Codex execution, credentials, or GUI
interaction:

| Area | Result |
| --- | --- |
| Backend non-live regression | `390 passed, 6 deselected, 2 xfailed` |
| Frontend Vitest | `52` files, `177` tests passed |
| Frontend typecheck/lint/build | PASS |
| Tauri cargo check | PASS |
| Tauri Rust tests | `31 passed, 0 failed` |
| Packaging and stress suite | `23 passed` |
| Packaged sidecar smoke | `2 passed`; readiness, healthz, authenticated system status, clean termination |
| Targeted regression after gate repairs | `10 passed` |
| Ruff | PASS for backend, desktop tests, and scripts |
| Strict mypy | PASS for `backend/src/codex_flow` (52 files) |
| Windows release build | Two NSIS-only idempotency runs passed; MSI/WiX was not rebuilt because the Windows Installer service remained unavailable |

The gate claims automated evidence only. Manual Desktop/UI checks remain
deferred to M12-REPORT-038.
