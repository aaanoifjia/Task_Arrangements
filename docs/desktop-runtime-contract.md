# Codex Flow Desktop Runtime Contract

## Scope

This document freezes the local Windows desktop boundary for Codex Flow. The
desktop application is a Tauri v2 shell around the existing React bundle and a
Python/PyInstaller backend sidecar. The shell is a presentation and process
owner; SQLite and the Python services remain the authoritative workflow state.

The desktop runtime does not read or modify Codex Desktop private databases,
LevelDB, renderer IPC, or other private state. Codex authentication continues
to use the real user `HOME`/`USERPROFILE` environment, inherited by the
sidecar.

## Process topology

```text
Tauri v2 process
├── React bundle (frontend/dist)
└── Python sidecar (packaged backend executable)
    ├── FastAPI/uvicorn local service
    ├── deterministic scheduler
    ├── SQLite durable state
    └── CodexAdapter
```

Tauri starts one sidecar for the application process. The sidecar is the only
process that owns workflow execution and persistence. The React bundle talks
to it through the loopback HTTP and WebSocket API already defined by the M8
API surface.

## Sidecar startup and stdout handshake

The sidecar is started with explicit runtime arguments for host, port,
database path, token, and log directory. Desktop mode always requests a
loopback host and uses an available local port. The sidecar must emit one
newline-delimited JSON readiness record on stdout after the service is bound:

```json
{"event":"ready","host":"127.0.0.1","port":43127,"token":"<process-local-token>"}
```

The `ready` record is the only startup signal the Tauri shell uses to publish
the API base URL and token to the React runtime. Malformed, duplicate, or
non-ready startup output is not treated as readiness; the shell reports a
startup failure and does not issue workflow requests.

The token is freshly generated for every sidecar process. It is held only in
process/runtime memory and is not persisted in SQLite, the install directory,
or a source-controlled configuration file.

## Loopback security

Desktop mode binds only to `127.0.0.1` (or the explicitly supported IPv6
loopback equivalent), never to a wildcard or LAN address. Every desktop REST
request and WebSocket connection carries the process-local token obtained from
the handshake. Requests with a missing or incorrect token are rejected before
application services run.

The token is a local process credential, not a user identity or a replacement
for Codex authentication. The Tauri shell is responsible for keeping it
inside the local runtime boundary and never exposing it through external
navigation or a public URL.

## App-data and logs

The sidecar receives absolute paths from the shell. Durable runtime data lives
under the current user's Windows local application-data directory, not beside
the installed executable:

```text
%LOCALAPPDATA%\Codex Flow\codex-flow.sqlite3
%LOCALAPPDATA%\Codex Flow\logs\backend.log
```

The exact platform path resolver may provide an equivalent per-user app-data
location, but the database and logs must remain user-writable and outside the
install directory. Workflow definitions, runs, attempts, events, and settings
continue to use the existing SQLite repositories and migrations.

## Graceful shutdown

Closing the Tauri window initiates an orderly shutdown: stop accepting new API
requests, ask the sidecar to shut down its service and scheduler, wait for the
sidecar process to exit, then let Tauri finish. The sidecar must flush durable
state and close SQLite before exit. If the bounded graceful wait expires, the
shell records the shutdown failure and terminates the child process as a last
resort; it does not silently claim that active external Codex work succeeded.

Restart/recovery remains governed by the existing durable reconciliation and
fail-closed scheduler semantics. The desktop shell never infers workflow
completion from process exit, stdout text other than the readiness handshake,
or elapsed time.

## Frozen boundary

- Tauri v2 owns the Windows shell and process lifecycle.
- React owns presentation only; it is not authoritative workflow state.
- The Python sidecar owns the local API, scheduler, CodexAdapter boundary, and
  SQLite state.
- The sidecar is loopback-only in desktop mode and protected by its fresh
  per-process token.
- Codex Desktop private storage and UI automation are outside this contract.
