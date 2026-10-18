# ADR-002: Codex adapter boundary

## Status
Accepted

## Context
Codex execution is an external integration and must not leak into scheduler control flow.

## Decision
Use a CodexAdapter boundary between the Scheduler and the OpenAI Codex SDK / App Server.

## Consequences
The Scheduler remains deterministic and testable; adapter implementations can evolve independently.
