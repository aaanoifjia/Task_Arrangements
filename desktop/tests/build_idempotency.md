# M11-BUILD-033-R1 — Installer-independent Build Idempotency Path

The existing desktop build script keeps the full Windows bundle pipeline as its
default (`-BundleTarget all`). It also accepts explicit `-BundleTarget nsis` and
`-BundleTarget msi` values, passed to the installed Tauri CLI as `--bundles
nsis` or `--bundles msi`. No WiX configuration, Windows Installer service, or
system feature is changed by the selector.

## Focused acceptance checks

The following offline parser/dry-run checks are required for this remediation:

```powershell
& .\scripts\build_desktop.ps1 -DryRun
& .\scripts\build_desktop.ps1 -DryRun -BundleTarget nsis
try { & .\scripts\build_desktop.ps1 -DryRun -BundleTarget invalid } catch { $_.Exception.Message }
```

Expected evidence:

- the default dry run prints `BUNDLE_TARGET: all` and the original Tauri build
  command without a `--bundles` selector;
- the NSIS dry run prints `BUNDLE_TARGET: nsis` and the Tauri build command with
  `--bundles nsis`;
- PowerShell rejects an invalid bundle target through the declared validation
  set;
- no build, download, installer-service operation, or system installation is
  performed by these checks.

## Recorded R1 validation

Run on 2026-10-22 with the existing user-level toolchain PATH temporarily
including `C:\Users\Administrator\.cargo\bin`:

```text
.\scripts\build_desktop.ps1 -DryRun
BUNDLE_TARGET: all
COMMAND: npm --prefix frontend exec tauri build -- --config desktop/src-tauri/tauri.conf.json

.\scripts\build_desktop.ps1 -DryRun -BundleTarget nsis
BUNDLE_TARGET: nsis
COMMAND: npm --prefix frontend exec tauri build -- --config desktop/src-tauri/tauri.conf.json --bundles nsis

.\scripts\build_desktop.ps1 -DryRun -BundleTarget invalid
Cannot validate argument on parameter 'BundleTarget'.
```

Both valid dry runs completed without invoking a build because `-DryRun` was
set. The invalid target was rejected before any build step. The default command
still selects the full configured Windows bundle pipeline; MSI/WiX support and
Windows Installer behavior were not changed.

## M11-BUILD-033 repeated-build evidence

Both idempotency runs used the same tracked repository state and the same
command:

```powershell
$env:Path = "C:\Users\Administrator\.cargo\bin;$env:Path"
.\scripts\build_desktop.ps1 -BundleTarget nsis
```

The tracked commit was `044284780ed5aa0aac66db308530ef0a9f260d94` for both
runs. Each run passed the frontend production build, PyInstaller sidecar
staging, Tauri release executable build, and NSIS bundling. The second-run
artifact discovery was:

| Artifact | Size (bytes) | SHA256 |
| --- | ---: | --- |
| `desktop/src-tauri/target/release/codex-flow-desktop.exe` | 9092096 | `252E70D3B0E511024AA51F20B4C4E3D642025025091121566D875F3C17D1AB47` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 7606028 | `BEEC88473C01738D8A94663532ED9B45293A4EC835AFB31D2E57D7D98695EE5A` |
| `desktop/src-tauri/binaries/codex-flow-server-x86_64-pc-windows-msvc.exe` | 5717136 | `FB71DA7602A7DECA0608D60C48EFCCDF889E48DBD6A6A77A6AADA2EA35F00F38` |

The second run rediscovered one current NSIS installer and one target-named
sidecar executable with one `_internal` runtime tree (369 files); no duplicate
staged sidecar was accumulated. The pre-existing MSI directory remains as
historical M9 evidence only and was not rebuilt or claimed as an M11 result.
The successful M9 MSI/NSIS evidence remains in
`docs/windows-build-artifacts.md`.

## Recorded R1 validation

Run on 2026-10-22 with the existing user-level toolchain PATH temporarily
including `C:\Users\Administrator\.cargo\bin`:

```text
.\scripts\build_desktop.ps1 -DryRun
BUNDLE_TARGET: all
COMMAND: npm --prefix frontend exec tauri build -- --config desktop/src-tauri/tauri.conf.json

.\scripts\build_desktop.ps1 -DryRun -BundleTarget nsis
BUNDLE_TARGET: nsis
COMMAND: npm --prefix frontend exec tauri build -- --config desktop/src-tauri/tauri.conf.json --bundles nsis

.\scripts\build_desktop.ps1 -DryRun -BundleTarget invalid
Cannot validate argument on parameter 'BundleTarget'.
```

Both valid dry runs completed without invoking a build because `-DryRun` was
set. The invalid target was rejected before any build step. The default command
still selects the full configured Windows bundle pipeline; MSI/WiX support and
Windows Installer behavior were not changed.
