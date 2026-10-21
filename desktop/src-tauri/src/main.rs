#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;

use std::sync::Mutex;

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let paths = sidecar::default_runtime_paths()?;
            let process = sidecar::launch_sidecar(&paths)?;
            app.manage(Mutex::new(process));
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Codex Flow desktop application");
}
