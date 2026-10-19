# Codex Flow M1 Compatibility Gate Report

Date: 2026-10-19

| Capability | Status | Evidence |
| --- | --- | --- |
| Python version | PASS | Python 3.11.9 from `auth_probe.json` |
| openai-codex version | PASS | `0.162.1` from `auth_probe.json` and `package_probe.json` |
| Runtime version if exposed | USER-CHECK | The M1 probe results do not record a separate bundled runtime version. |
| Windows version | PASS | `Windows-10-10.0.19045-SP0` from `auth_probe.json` |
| Account access | PASS | `account_access_ok = true` from `auth_probe.json` |
| Thread start | PASS | Basic probe recorded thread `01a150bf-f9d8-7dc3-a0a9-d08d188e265b`. |
| Turn start | PASS | Basic probe observed `turn/started`. |
| Event stream | PASS | Basic probe recorded public stream events through `turn/completed`. |
| Terminal event | PASS | Basic probe observed `turn/completed` with status `completed`. |
| Workspace write | PASS | Basic probe verified exact `OUTPUT.txt` content with no unexpected files. |
| Resume | PASS | Control probe extracted `CODEX_FLOW_RESUME_MARKER_7F31` from the resumed second turn. |
| Interrupt | PASS | Control probe requested interruption and received terminal status `interrupted`. |
| Deep link launch | PASS | Desktop interop probe generated and launched the real thread deep link. |
| Desktop sidebar behavior | PASS | User verified opening, correct thread, sidebar visibility, searchability, and project association. |
| PyInstaller probe | PASS | Frozen probe executable exited 0 and printed `sdk_version=0.162.1` and `account_access_ok=true`. |

## M2 Gate

All M2 hard-gate capabilities are PASS: account access, thread start, turn start, terminal event, workspace write, resume, and interrupt. The project may proceed to the internal Codex adapter contract.

Desktop sidebar behavior and PyInstaller are recorded as compatibility evidence and are not M2 hard gates.
