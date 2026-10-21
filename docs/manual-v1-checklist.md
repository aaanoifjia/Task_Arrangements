# Codex Flow v1 Manual Verification Checklist

Status: PENDING user verification after the automated M10 beta gate.

Use the packaged Windows artifacts recorded in
[`windows-build-artifacts.md`](windows-build-artifacts.md). Record the date,
artifact filename, and observation for every item. Do not mark an item PASS
from automated test output alone.

## Installer and runtime

- [ ] Launch the authoritative Windows installer successfully.
- [ ] Installed Codex Flow starts without an unexpected sidecar process error.
- [ ] The packaged sidecar reaches readiness and the normal route becomes usable.
- [ ] Closing the application terminates the sidecar cleanly.

## V1 workflow interaction

- [ ] Create a new workflow in the packaged application.
- [ ] Create multiple task nodes, enter complete prompts, set working directories,
      and draw dependency edges.
- [ ] Save the workflow, reload or navigate away/back, and confirm the saved
      definition is present.
- [ ] Start a workflow and observe run history and task status updates.
- [ ] Exercise Pause, Resume, Retry, and Cancel from the visible controls.
- [ ] Restart the application and confirm durable run history/recovery behavior
      without duplicate execution.

## Native/Desktop behavior

- [ ] Observe the native human-attention notification appearance.
- [ ] Use Open in Codex for a real thread and confirm the expected Codex Desktop
      thread opens.
- [ ] Confirm the thread appears in the sidebar without restarting Codex Desktop.
- [ ] Confirm the thread is searchable and associated with the expected project.
- [ ] Observe a multi-task workflow and confirm no manual Enter is required
      between tasks.

## Evidence handoff

- Verification date: ____________________
- Tester: ______________________________
- Installer artifact: ___________________
- Notes / screenshots / thread IDs: ______

Manual-only or both-mode items remain pending until this checklist is completed
by the user. Any failure should be recorded as a blocker with the exact step,
artifact, and observed error.
