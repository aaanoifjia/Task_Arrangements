# Windows Build Artifacts

M9-DESKTOP-038 was built on 2026-10-22 with the repository's installed
Tauri CLI 2.12.4, Rust stable MSVC toolchain, Node/npm, and project Python
environment. The authoritative command was:

```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
.\scripts\build_desktop.ps1
```

The frontend production build, PyInstaller sidecar build/staging, Tauri
release executable, MSI bundle, and NSIS installer all completed successfully.
The bundle outputs are reproducible from the committed Tauri configuration,
build script, sidecar builder, and temporary engineering icon source.

| Artifact | Size (bytes) | SHA256 |
| --- | ---: | --- |
| `desktop/src-tauri/target/release/codex-flow-desktop.exe` | 9129984 | `24ABCCBA13E21857275965A829D0C19F7C90946AC651DB6857EAFC29EA6190AA` |
| `desktop/src-tauri/target/release/bundle/msi/Codex Flow_0.1.0_x64_en-US.msi` | 8585216 | `F6B1406510F98394E8AC2ED6E373DFB4B579F4C221ECA7911439C1F2C80E51AE` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 7604381 | `69E57CE1DE444D617F5D59A8214DD82C3377DED244DEFB46224F53F982CFB324` |

This task records automated build evidence only; installer launch, visual UX,
and other manual Desktop checks are intentionally deferred. The read-only
manifest verifier checks every table row's repository-relative path, byte size,
and SHA256 without rebuilding or downloading artifacts.
