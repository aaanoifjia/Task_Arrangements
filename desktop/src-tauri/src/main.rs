#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;
mod runtime_state;
mod paths;
mod open_external;
mod single_instance;

use std::time::Duration;
use std::sync::Mutex;

use tauri::{Manager, RunEvent};

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            single_instance::focus_existing_window(app);
        }))
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
        .invoke_handler(tauri::generate_handler![runtime_state::runtime_state, open_external::open_external])
        .build(tauri::generate_context!())
        .expect("error while building Codex Flow desktop application");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            if let Some(process) = app_handle.try_state::<Mutex<sidecar::SidecarProcess>>() {
                if let Ok(mut process) = process.lock() {
                    let _ = process.shutdown();
                }
            }
        }
    });
}
