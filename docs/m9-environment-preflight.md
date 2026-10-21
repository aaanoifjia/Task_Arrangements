# M9 Windows Desktop Toolchain Preflight

Date: 2026-10-22 (Asia/Shanghai)

Result: **PASS** after installing the explicitly authorized official Rust
toolchain. No Visual Studio Build Tools, Windows SDK, WebView2, or other
system component was installed by this preflight.

## Declared prerequisite evidence

| Prerequisite | Result | Evidence |
| --- | --- | --- |
| Python 3.11+ and project virtual environment | PASS | `\.venv\Scripts\python.exe --version` → `Python 3.11.9`; `\.venv\Scripts\python.exe` exists. |
| PyInstaller from project environment | PASS | `\.venv\Scripts\python.exe -m PyInstaller --version` → `6.22.3`. |
| Node | PASS | `C:\Program Files\nodejs\node.exe`; `node --version` → `v24.20.0`. |
| npm | PASS | `C:\Program Files\nodejs\npm.ps1`; `npm --version` → `11.19.0`. |
| rustup | PASS | `C:\Users\Administrator\.cargo\bin\rustup.exe`; `rustup --version` → `rustup 1.29.2 (d8c92c676 2026-10-21)`. |
| cargo | PASS | `C:\Users\Administrator\.cargo\bin\cargo.exe`; `cargo --version` → `cargo 1.99.1 (5f94df478 2026-08-27)`. |
| rustc | PASS | `C:\Users\Administrator\.cargo\bin\rustc.exe`; `rustc --version` → `rustc 1.99.1 (58cf8f9c3 2026-10-13)`. |
| Microsoft C++/MSVC build tools | PASS | `C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json` returned the complete Visual Studio 2022 Build Tools instance; installation version `17.14.37710.0`, MSVC toolset `14.44.35207`. |
| Windows SDK | PASS | `C:\Program Files (x86)\Windows Kits\10\Include` contains `10.0.19041.0` and `10.0.26100.0`; matching Windows Kits bin roots are present. |
| WebView2 Runtime | PASS | `C:\Program Files (x86)\Microsoft\EdgeWebView\Application\155.0.4283.62` exists. |
| Git | PASS | `C:\Program Files\Git\cmd\git.exe`; `git --version` → `git version 2.55.0.windows.5`. |

## Authorized Rust installation

Initial audit found `cargo`, `rustc`, and `rustup` missing. The current user
invocation explicitly authorized the exact named Rust toolchain, so the
official Rustup installer was downloaded from `https://win.rustup.rs/x86_64`
and run as the current user with:

```text
rustup-init.exe -y --default-toolchain stable --profile minimal
```

The installer exited `0`, installed the default host
`x86_64-pc-windows-msvc`, and reported stable `rustc 1.99.1`. The current
process PATH was refreshed with `%USERPROFILE%\.cargo\bin` before the version
verification above. No elevation, reboot, GUI installer flow, license
interaction, or adjacent system installation was performed.

## Resume decision

All declared M9 preflight prerequisites are present. The prior
`M9-DESKTOP-003` environment blocker is cleared and that task is the next
task to resume automatically.
