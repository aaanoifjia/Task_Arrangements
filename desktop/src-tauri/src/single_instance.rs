use tauri::{AppHandle, Manager};

const MAIN_WINDOW_LABEL: &str = "main";

pub fn focus_existing_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window(MAIN_WINDOW_LABEL) {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

#[cfg(test)]
mod tests {
    use super::MAIN_WINDOW_LABEL;

    #[test]
    fn second_instance_targets_the_existing_main_window() {
        assert_eq!(MAIN_WINDOW_LABEL, "main");
    }
}
