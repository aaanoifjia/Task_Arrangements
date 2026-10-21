#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;
mod runtime_state;
mod paths;
mod open_external;
mod single_instance;
mod window_state;

use std::time::Duration;
use std::sync::Mutex;

use tauri::{Manager, PhysicalPosition, PhysicalSize, RunEvent, WindowEvent};

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            single_instance::focus_existing_window(app);
        }))
        .setup(|app| {
            let runtime_paths = paths::resolve_runtime_paths(app.handle())?;
            app.manage(runtime_paths);
            let main_window = app
                .get_webview_window("main")
                .ok_or_else(|| std::io::Error::other("main window missing"))?;
            let window_state_path = app
                .path()
                .app_data_dir()
                .map_err(|error| std::io::Error::other(error.to_string()))?
                .join("window-state.json");
            if let Ok(Some(saved)) = window_state::load(&window_state_path) {
                let saved = window_state::clamp(saved, window_state::ScreenBounds::default());
                let _ = main_window.set_size(PhysicalSize::new(saved.width, saved.height));
                let _ = main_window.set_position(PhysicalPosition::new(saved.x, saved.y));
                if saved.maximized { let _ = main_window.maximize(); }
            }
            let persist_path = window_state_path.clone();
            let persist_window = main_window.clone();
            main_window.on_window_event(move |event| {
                if !matches!(event, WindowEvent::CloseRequested { .. }) { return; }
                if let (Ok(position), Ok(size), Ok(maximized)) = (
                    persist_window.outer_position(),
                    persist_window.inner_size(),
                    persist_window.is_maximized(),
                ) {
                    let state = window_state::WindowState {
                        x: position.x,
                        y: position.y,
                        width: size.width,
                        height: size.height,
                        maximized,
                    };
                    let _ = window_state::save(&persist_path, &state);
                }
            });
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
