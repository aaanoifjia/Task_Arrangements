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
| `desktop/src-tauri/target/release/bundle/msi/Codex Flow_0.1.0_x64_en-US.msi` | 8585216 | `DE244EEBFCC22E5550F7DEED77727495F594C715F122EB6420F070A2A5565D23` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 7603613 | `BA8B315FBFF0302274CDDC1FB2B96B0B038C0413724D33332EA4EEC32141A46C` |

The release executable was also produced at
`desktop/src-tauri/target/release/codex-flow-desktop.exe`. This task records
automated build evidence only; installer launch, visual UX, and other manual
Desktop checks are intentionally deferred.
