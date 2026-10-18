# ADR-008: Same-workspace write lock

## Status
Accepted

## Context
Concurrent write tasks in one working directory can interfere with one another.

## Decision
Serialize workspace-write tasks sharing the same canonical workspace key, while allowing independent workspaces to proceed concurrently.

## Consequences
Dangerous same-workspace overlap is prevented in the local scheduler layer; read-only work is not unnecessarily serialized.
