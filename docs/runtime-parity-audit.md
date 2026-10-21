# Runtime Parity Audit

Updated: 2026-10-22

M10-HARDEN-001 compares the durable `DurableRunner`/`RuntimeManager` path with
the frozen `AsyncScheduler` semantics. The audit is deliberately limited to
known contract differences and does not propose speculative architecture
changes.

## Audit result

The audit test file is `backend/tests/integration/test_runtime_parity.py`.
Known gaps are represented as strict `xfail` tests so they fail before the
corresponding authoritative hardening task and become ordinary passing tests
when that task closes the gap. M10-HARDEN-002 has now closed the continuation
gap, so its audit test is an ordinary passing test.

| Frozen behavior | Current durable result | Follow-up |
| --- | --- | --- |
| `CONTINUE_THREAD` resumes the successful source thread and starts a new turn | PASS: durable runner validates the successful source and calls `resume_thread` before the distinct new turn | M10-HARDEN-003/004 |
| Independent ready work may run concurrently under a configured global limit | Known gap: durable runner is sequential and has no configured concurrency setting | M10-HARDEN-005/006 and M10-HARDEN-011 |
| Same-workspace writes remain serialized | PASS conservatively: current runner serializes all tasks; no concurrent same-workspace writes occur | M10-HARDEN-007 and M10-HARDEN-010 add the explicit durable lock contract |
| One active turn per Codex thread | Not independently exercisable until durable continuation exists; continuation gap is the blocking known gap | M10-HARDEN-002 and M10-HARDEN-008 |
| Retry preserves prior attempts and re-evaluates downstream readiness | PASS: existing durable retry/dependency tests and parity regression preserve the blocked-child rule | M10-HARDEN-013 through M10-HARDEN-018 cover automatic retry semantics |
| Explicit command/tool failure prevents downstream readiness | PASS: terminal stream consumes `TURN_COMPLETED` and maps failed command details to `FAILED` | M10-HARDEN-012 covers transient classification without weakening this rule |
| Task timeout is enforced and fails closed | Known gap: `timeout_seconds` is present in the model but not enforced by durable execution | M10-HARDEN-019 through M10-HARDEN-021 |

## Acceptance

The audit identifies only behavior directly required by the frozen scheduler
contract and mapped to the next authoritative M10 tasks. No production files
or dependencies were changed by this audit.
