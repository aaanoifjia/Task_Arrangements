# ADR-006: Tauri desktop shell

## Status
Accepted

## Context
Codex Flow is intended to run as a local desktop application with a Python backend.

## Decision
Use Tauri with a Python sidecar for the later desktop shell.

## Consequences
The desktop shell hosts the UI and local backend while durable workflow state remains in SQLite.
