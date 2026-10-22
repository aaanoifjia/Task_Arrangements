# Codex Flow — M11 Release Candidate Test Report

Recorded: 2026-10-22  
Scope: offline/local M11 release-candidate validation

## Result

M11 automated acceptance PASS. The repository-controlled release candidate
checks passed without live Codex execution, external web research, new package
downloads, new runtime dependencies, new system toolchains, credentials, or
manual GUI interaction.

## Commands and results

All Python commands used `\.venv\Scripts\python.exe`. Pytest used dedicated
directories under the ignored `backend/.pytest-tmp/` path.

| Area | Command/result |
| --- | --- |
| Backend regression | `\.venv\Scripts\python.exe -m pytest backend/tests -q -m "not live_codex" --basetemp backend/.pytest-tmp/m11-gate-035-backend` — **390 passed, 6 deselected, 2 xfailed** |
| Frontend tests | `npm --prefix frontend run test:run` — **52 files, 177 tests passed** |
| Frontend typecheck | `npm --prefix frontend run typecheck` — **PASS** |
| Frontend lint | `npm --prefix frontend run lint` — **PASS** |
| Frontend production build | `npm --prefix frontend run build` — **PASS** |
| Tauri compile | `cargo check --manifest-path desktop/src-tauri/Cargo.toml` — **PASS** |
| Tauri Rust tests | `cargo test --manifest-path desktop/src-tauri/Cargo.toml` — **31 passed, 0 failed** |
| Packaging/stress | `\.venv\Scripts\python.exe -m pytest backend/tests/packaging backend/tests/stress -q -m "not live_codex" --basetemp backend/.pytest-tmp/m11-gate-035-packaging-stress` — **23 passed** |
| Packaged sidecar smoke | `\.venv\Scripts\python.exe -m pytest backend/tests/packaging/test_packaged_sidecar_contract.py --basetemp backend/.pytest-tmp/m11-build-034-r1` — **2 passed** |
| Targeted regression | `\.venv\Scripts\python.exe -m pytest backend/tests/contracts/test_fake_adapter.py backend/tests/unit/test_workflow_service.py -q --basetemp backend/.pytest-tmp/m11-gate-035-targeted` — **10 passed** |
| Ruff | `\.venv\Scripts\python.exe -m ruff check backend/src/codex_flow backend/tests desktop/tests scripts` — **PASS** |
| Strict mypy | `\.venv\Scripts\python.exe -m mypy --strict backend/src/codex_flow` — **52 source files, PASS** |

## Build and installer evidence

The default full bundle pipeline remains unchanged. Because the host Windows
Installer service continued to fail WiX ICE validation with Win32 `0x643`, the
M11 repeated-build task used the explicit installed-Tauri-CLI NSIS mode twice:

```powershell
$env:Path = "C:\Users\Administrator\.cargo\bin;$env:Path"
.\scripts\build_desktop.ps1 -BundleTarget nsis
.\scripts\build_desktop.ps1 -BundleTarget nsis
```

Both runs used tracked commit `044284780ed5aa0aac66db308530ef0a9f260d94` and
passed frontend build, PyInstaller sidecar build/staging, release executable
build, and NSIS bundling. The second-run artifacts were:

| Artifact | Size (bytes) | SHA256 |
| --- | ---: | --- |
| `desktop/src-tauri/target/release/codex-flow-desktop.exe` | 9092096 | `252E70D3B0E511024AA51F20B4C4E3D642025025091121566D875F3C17D1AB47` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 7606028 | `BEEC88473C01738D8A94663532ED9B45293A4EC835AFB31D2E57D7D98695EE5A` |
| `desktop/src-tauri/binaries/codex-flow-server-x86_64-pc-windows-msvc.exe` | 5717136 | `FB71DA7602A7DECA0608D60C48EFCCDF889E48DBD6A6A77A6AADA2EA35F00F38` |

MSI was **not rebuilt during M11**. The existing successful M9 MSI/NSIS
evidence remains in `docs/windows-build-artifacts.md` and is not represented as
a fresh M11 MSI result. No Windows service, optional feature, firewall/security
setting, or system installer was modified.

## Resolved bounded remediations

- `M11-BUILD-033-R1` added `-BundleTarget all|nsis|msi` to
  `scripts/build_desktop.ps1`. `all` remains the default; dry-run checks cover
  default, NSIS, and invalid selector behavior.
- `M11-BUILD-034-R1` replaced the generated Tauri `_internal` staging tree
  before copying the current PyInstaller runtime. This removed nested
  `_internal/_internal` ambiguity and restored migration discovery.
- The gate applied only directly implicated, behavior-neutral test/type
  hygiene repairs: one RUF015 assertion, explicit snapshot `cast`, and import
  formatting. No architecture, dependency, or public runtime contract changed.

## Remaining manual checks

Manual Desktop/UI verification remains intentionally deferred until
`M12-REPORT-038`. This report makes no claims about installer launch visuals,
window behavior, notifications, Codex Desktop interoperability, or final user
workflow observation.

## M12 handoff

M11 automated validation is complete. The deterministic next task is
`M12-UX-001`.
