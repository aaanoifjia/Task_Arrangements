# M1-HOME-FIX-001 — Fix Codex Runtime Home Directory Environment

## Goal

Fix the existing Codex execution probes so the SDK-launched Codex runtime can locate a Windows home directory, without changing SDK version, transport architecture, or product code.

## Dependencies

- PREP-000 COMPLETE
- existing M1 probe scripts present

## Current Evidence

`spikes/codex_execution_probe/results/basic_execution.json` currently records:

```text
TransportClosedError: Codex process closed stdout.
WARNING: proceeding, even though we could not create PATH aliases:
Could not find home directory
Error: Could not find home directory
```

The current task is only to diagnose and repair that environment handoff.

## Owned Files

Allowed:
- `spikes/codex_execution_probe/home_environment_probe.py`
- `spikes/codex_execution_probe/results/home_environment.json`
- `spikes/codex_execution_probe/basic_execution_probe.py`
- `spikes/codex_execution_probe/auth_probe.py`
- `spikes/codex_execution_probe/resume_interrupt_probe.py`

Do not modify backend product code, pyproject dependencies, Desktop private state, or canonical architecture docs.

## Steps

1. Create `home_environment_probe.py`.
2. Record only non-secret home-related environment diagnostics:
   - `HOME`
   - `USERPROFILE`
   - `HOMEDRIVE`
   - `HOMEPATH`
   - `Path.home()`
   - `os.path.expanduser("~")`
   - whether each resolved directory exists
3. Write diagnostics to `results/home_environment.json`.
4. Determine the canonical home value using this exact order:
   - existing non-empty `USERPROFILE` that points to an existing directory;
   - existing non-empty `HOME` that points to an existing directory;
   - `Path.home()` if it resolves to an existing directory;
   - existing `HOMEDRIVE + HOMEPATH`.
5. If no valid directory exists, mark the task BLOCKED. Do not invent/create a fake home directory.
6. Add one small helper in each M1 probe script, before constructing `Codex`/`AsyncCodex`:
   - set `USERPROFILE` to the canonical home only if missing/empty;
   - set `HOME` to the same canonical home only if missing/empty;
   - do not delete or overwrite an existing non-empty value;
   - do not modify global Windows environment variables or registry.
7. Run the environment probe.
8. Re-run the existing authentication probe.
9. Re-run the basic execution probe.
10. If basic execution reaches a real terminal event and verifies the exact output file, re-run the resume/interrupt probe.
11. Preserve all result JSON diagnostics.

## Acceptance

PASS only if:
- a valid existing Windows home directory is identified;
- probe scripts explicitly ensure child-process HOME/USERPROFILE are present;
- authentication probe no longer fails from missing home;
- basic execution no longer reports `Could not find home directory`;
- basic execution reaches a real terminal event and verifies output.

If the home-directory error disappears but another Codex error occurs, this task is COMPLETE as an environment fix only when the new error proves the child runtime passed home discovery. Record the new blocker precisely in progress; do not redesign transport.

## Tests

Run the three probe scripts using:

```powershell
.\.venv\Scripts\python.exe <script>
```

Do not use sleep-based completion, UI automation, WSL, another SDK, or Desktop private databases.
