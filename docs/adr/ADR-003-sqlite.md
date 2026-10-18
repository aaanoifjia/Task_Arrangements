# ADR-003: SQLite local state

## Status
Accepted

## Context
Workflow execution must survive UI restarts and retain durable history locally.

## Decision
Use SQLite as the authoritative durable local state store.

## Consequences
State and audit history are local and queryable. Codex Desktop state is not treated as authoritative.
