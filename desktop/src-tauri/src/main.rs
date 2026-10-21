#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;
mod runtime_state;
mod paths;

use std::time::Duration;
use std::sync::Mutex;

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let runtime_paths = paths::resolve_runtime_paths(app.handle())?;
            app.manage(runtime_paths);
            let paths = sidecar::default_runtime_paths()?;
            let process = sidecar::launch_sidecar(&paths)?;
            let readiness = sidecar::wait_for_readiness(
                &process.output,
                Duration::from_secs(10),
            )
            .map_err(|error| std::io::Error::other(format!("sidecar handshake failed: {error:?}")))?;
            let state = runtime_state::RuntimeState::from_readiness(
                &readiness,
                process.token.clone(),
            );
            app.manage(runtime_state::RuntimeStateStore::ready(state));
            app.manage(Mutex::new(process));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![runtime_state::runtime_state])
        .run(tauri::generate_context!())
        .expect("error while running Codex Flow desktop application");
}
