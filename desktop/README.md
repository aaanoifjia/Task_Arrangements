# Codex Flow Desktop

The `desktop/` directory contains the Tauri v2 Windows shell for Codex Flow.
The shell packages the React production bundle and launches the Python backend
as a sidecar executable.

The frozen runtime contract is documented in
[`docs/desktop-runtime-contract.md`](../docs/desktop-runtime-contract.md).

## Runtime boundary

- Tauri owns the desktop window and sidecar lifecycle.
- React is loaded from the frontend bundle and communicates with the sidecar
  over authenticated loopback HTTP/WebSocket connections.
- The Python sidecar owns FastAPI, the deterministic scheduler, SQLite, and
  the `CodexAdapter` boundary.
- SQLite and logs are stored under the user's local app-data directory, never
  in the installation directory.
- The sidecar emits a single JSON `ready` handshake on stdout after binding.
- A fresh per-process local token protects the desktop API.

Desktop implementation files are added in the following M9 tasks. This task
only freezes the contract and does not install Rust, build a Windows
installer, or access private Codex Desktop state.

## Production bundle wiring

The Tauri configuration uses `frontend/dist` as `frontendDist` and runs the
frontend build before `tauri build`. Vite emits relative asset URLs so the
same bundle works from the Tauri asset protocol. The frontend does not bake a
backend URL into the production bundle: in desktop mode it loads the runtime
base URL and bearer token through the Tauri `runtime_state` bridge, while the
browser path continues to use its current origin.
