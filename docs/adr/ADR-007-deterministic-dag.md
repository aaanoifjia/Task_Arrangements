# ADR-007: Deterministic DAG scheduling

## Status
Accepted

## Context
Task dependencies and workflow progression must be predictable and auditable.

## Decision
Use an explicitly defined, validated DAG with deterministic fail-closed readiness and state transitions. Do not use an LLM as a control plane.

## Consequences
Invalid graphs are rejected, ambiguous completion does not release downstream work, and progression is reproducible.
