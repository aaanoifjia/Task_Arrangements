# Codex Flow V1 Manual Smoke Test Report

Test round: 1  
Platform: Windows 10 x64  
Artifact: `Codex Flow_0.1.0_x64-setup.exe`  
Artifact SHA256: `D220D3EA9DBFA3336D0272D98100A7803BB7810B3519F108571E4378E543B008`

## Round 1 — SMOKE-WIN-001

Step: Launch the installed Codex Flow desktop application.

Expected: The application window remains open, the packaged sidecar reaches
readiness, and the normal UI becomes usable.

Observed: The installed Codex Flow application opens and immediately
exits/crashes before the normal UI becomes usable.

Result: **FAIL**

Status: **UNDER INVESTIGATION**

The original failure is preserved as the baseline and must not be replaced by
post-fix evidence. The remaining manual checklist is not marked PASS by this
report.
