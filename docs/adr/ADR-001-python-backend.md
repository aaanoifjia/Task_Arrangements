# ADR-001: Python backend

## Status
Accepted

## Context
Codex Flow needs a local execution core for deterministic scheduling and integration boundaries.

## Decision
Implement the backend in Python.

## Consequences
The backend can provide typed domain logic and asynchronous execution. The local API and desktop shell remain later layers.
