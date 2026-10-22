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
