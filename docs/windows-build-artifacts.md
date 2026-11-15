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

## M13-02 current-build evidence — 2026-11-14

The formal command `scripts/build_desktop.ps1 -BundleTarget nsis` completed
after the exclusive TEMP lock was verified available. The lock was released at
completion. The build included the frontend production build, PyInstaller
sidecar staging, bundled Codex CLI, Tauri release build, NSIS package, and the
script's marker-aware payload gate.

| Artifact | SHA256 |
| --- | --- |
| NSIS installer | `F0EB88A6FDE1FA20D3A97E6A3EC7E2344D3DA2A4DCFCF1BDBD6DFD7FC87040F7` |
| Release EXE | `B73A89E8AB460F557099A2D09D8EFB0EB4F2C34D90BDB34D6FE2C978D846FA47` |
| Extracted NSIS payload EXE | `D15777B8742F8CE4A93DF1D9D43B7B855484EB2318E061B9CDDD8DFE03F84FEE` |

The normalized release-to-payload comparison passed at marker offset `6909610`
(`UNK` in the release executable versus the expected `NSS` installer marker).

The installer was then run normally in silent mode and returned exit code 0.
However, the installed executable remained
`8D445638C50726E5FF7E0F4BC44738D81C67CD8EF0C883B47B2F33B7002F96A9`, not the
current payload hash. A pre-existing installed Codex Flow process held the
executable and was not test-owned, so it was deliberately not terminated.
This is a blocked install identity gate, not a successful installation.

### M13-02-R1 resolved install identity

Payload inspection was corrected to preserve both NSIS registry keys that it
temporarily changes: the uninstall registration and the install-mode directory
key. After a clean rebuild, the normal silent installer selected the standard
`%LOCALAPPDATA%\Codex Flow` path. An independent temporary extraction, with
both keys backed up and restored, produced this verified identity:

| Artifact | SHA256 |
| --- | --- |
| NSIS installer | `A00540179D4DBF301567B6A3F30B4D32D6BDF76A875B4BD5CEB00B25EBECF207` |
| Extracted NSIS payload EXE | `8371CE38E0E230E72D803D8E0A940495F961FCA9C35B53DDAF84BEDE4FFD11E4` |
| Installed EXE | `8371CE38E0E230E72D803D8E0A940495F961FCA9C35B53DDAF84BEDE4FFD11E4` |
