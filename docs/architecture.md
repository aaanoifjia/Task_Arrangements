# Codex Flow Architecture

The system is a local-first Python backend with a future desktop presentation layer:

```text
UI
↓
Local API
↓
Application Services
↓
Scheduler
↓
CodexAdapter
↓
OpenAI Codex SDK / App Server
```

SQLite is the authoritative durable local state. The backend is Python; FastAPI is planned for the local API, React and React Flow for the future UI, and Tauri with a Python sidecar for the future desktop shell.

CodexAdapter is the integration boundary. Scheduler code never calls the SDK directly. Desktop UI is not authoritative state, and the core contains no browser/Desktop RPA and no master-agent scheduling.

The scheduler uses a deterministic, fail-closed DAG, asynchronous backend execution, and a same-workspace write lock.

## Non-goals

- No multi-user cloud.
- No automatic dependency inference.
- No prompt rewriting.
- No private Codex Desktop database access.
- No LangGraph control plane.
