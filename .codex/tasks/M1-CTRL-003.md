# M1-CTRL-003 — Resume + Interrupt Control Probe

## Goal

Validate the two Codex control capabilities required by Codex Flow:

1. A persisted Codex thread can be resumed in a new `AsyncCodex` context and retains prior conversational context.
2. An active Codex turn can be interrupted through the public SDK and produces a real interrupted terminal event.

The interrupt half is already passing in the current probe. The remaining known defect is response extraction for the resumed second turn: the turn completes, but `second_response` is currently empty.

Do not redesign the probe. Repair the existing public-event response extraction and re-run the full control probe.

## Dependencies

Must already be COMPLETE:

- PREP-000
- M1-HOME-FIX-001
- M1-AUTH-001
- M1-RUN-002

Required SDK:

```text
openai-codex==0.162.1
```

## Current Evidence

Current `resume_interrupt.json` shows:

```text
resume:
  first_terminal_status = completed
  second_turn_id = present
  second_response = ""
  resume_verified = false

interrupt:
  interrupt_requested = true
  interrupt_event_received = true
  interrupt_terminal_status = interrupted
```

Therefore:
- thread creation works;
- first turn completes;
- thread resume returns a usable thread;
- second turn completes;
- interrupt works;
- the remaining resume blocker is extraction of the second turn's agent-message text.

## Owned Files

Only modify:

```text
spikes/codex_execution_probe/resume_interrupt_probe.py
spikes/codex_execution_probe/results/resume_interrupt.json
spikes/codex_execution_probe/workspaces/control/*
.codex/progress.json
docs/current-progress.md
```

Do not modify:

```text
backend/
backend/pyproject.toml
docs/reference/
AGENTS.md
other probe scripts
```

## Execution Steps

### 1. Verify SDK

Run:

```powershell
.\.venv\Scripts\python.exe -m pip show openai-codex
```

Require:

```text
Version: 0.162.1
```

If not, BLOCK. Do not change package versions.

### 2. Preserve the existing home-environment repair

Keep the existing local `ensure_home_environment()` behavior.

Do not modify global Windows environment variables, registry settings, or user profile configuration.

### 3. Repair public event response extraction

The existing `consume()` function incorrectly relies on `payload.item.text` for the resumed agent response.

Update `consume()` using only public event payload fields:

- When `event.method == "item/agentMessage/delta"`:
  - read `payload.delta`;
  - if it is a string, append it to `delta_parts`.
- Continue to inspect completed item text only as a fallback:
  - if `payload.item.text` is a string, collect it separately in `completed_message_parts`.
- At the end of the stream:
  - if `delta_parts` is non-empty, response is `"".join(delta_parts)`;
  - otherwise response is `"".join(completed_message_parts)`.

Do not dump private SDK objects.
Do not inspect underscored/private attributes.
Do not infer the response from files or logs.

### 4. Resume test

Use the existing exact marker:

```text
CODEX_FLOW_RESUME_MARKER_7F31
```

First `AsyncCodex` context:

1. Create a new thread in `workspaces/control/resume` using `Sandbox.workspace_write`.
2. Send:

```text
Remember this exact marker for this thread:

CODEX_FLOW_RESUME_MARKER_7F31

Reply only with:
ACK
```

3. Fully consume the first turn to a real terminal event.
4. Save:
   - `thread_id`
   - `first_turn_id`
   - `first_terminal_status`
5. Exit the first `AsyncCodex` context completely.

Second, new `AsyncCodex` context:

1. Resume with:

```python
thread = await codex.thread_resume(thread_id)
```

2. Send:

```text
Reply with only the exact marker I told you to remember earlier in this thread.
```

3. Fully consume the second turn to a real terminal event.
4. Save:
   - `second_turn_id`
   - `second_response`
   - `resume_verified`

`resume_verified` is true only if:

```text
CODEX_FLOW_RESUME_MARKER_7F31
```

is present in the actual extracted second-turn response.

### 5. Interrupt test

Use a separate thread in:

```text
workspaces/control/interrupt
```

Prompt:

```text
Count from 1 to 100000, one integer per line.
Do not summarize.
Do not skip numbers.
```

Begin consuming the real stream.

Only after receiving a real started/running signal, call:

```python
await turn.interrupt()
```

Do not use a fixed long sleep.

Continue consuming the same stream until the terminal event.

Record:

- `thread_id`
- `turn_id`
- `interrupt_requested`
- `interrupt_event_received`
- `interrupt_terminal_status`

`interrupt_event_received` may be true only when the actual terminal event reports interrupted semantics.

### 6. Result JSON

Write:

```text
spikes/codex_execution_probe/results/resume_interrupt.json
```

with at least:

```json
{
  "resume": {
    "thread_id": "...",
    "first_turn_id": "...",
    "first_terminal_status": "completed",
    "second_turn_id": "...",
    "second_response": "CODEX_FLOW_RESUME_MARKER_7F31",
    "resume_verified": true
  },
  "interrupt": {
    "thread_id": "...",
    "turn_id": "...",
    "interrupt_requested": true,
    "interrupt_event_received": true,
    "interrupt_terminal_status": "interrupted"
  }
}
```

Do not store secrets.

### 7. Run the probe

Run:

```powershell
.\.venv\Scripts\python.exe spikes\codex_execution_probe\resume_interrupt_probe.py
```

The process must exit 0.

Then inspect:

```powershell
Get-Content spikes\codex_execution_probe\results\resume_interrupt.json
```

## Acceptance Criteria

PASS only when all are true:

```text
first_terminal_status = completed
second_turn_id is non-empty
second_response contains CODEX_FLOW_RESUME_MARKER_7F31
resume_verified = true

interrupt_requested = true
interrupt_event_received = true
interrupt_terminal_status = interrupted

probe process exit code = 0
```

Do not treat a completed second turn with an empty extracted response as success.

## Completion

After PASS:

1. Mark `M1-CTRL-003` COMPLETE in `.codex/progress.json`.
2. Clear `active_task`.
3. Set `next_task` to the next dependency-ready task according to the recorded plan. With M1-AUTH-001, M1-RUN-002, and M1-CTRL-003 complete, the next deterministic task is `M1-PACK-005`.
4. Update `docs/current-progress.md`.
5. Commit the task according to `AGENTS.md`.

## Out of Scope

Do not:

- upgrade/downgrade `openai-codex`;
- change transport architecture;
- use Codex Desktop UI automation;
- read or modify private Codex Desktop databases;
- use WSL as a workaround;
- implement `CodexAdapter`;
- implement Scheduler product code;
- modify unrelated probes;
- change the marker or acceptance semantics.
