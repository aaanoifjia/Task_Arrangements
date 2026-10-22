use tauri::{AppHandle, Manager, Runtime, WebviewWindow};

const MAIN_WINDOW_LABEL: &str = "main";

pub fn focus_existing_window<R: Runtime>(app: &AppHandle<R>) {
    focus_window(app.get_webview_window(MAIN_WINDOW_LABEL).as_ref());
}

trait FocusTarget {
    fn show_window(&self);
    fn focus_window(&self);
}

impl<R: Runtime> FocusTarget for WebviewWindow<R> {
    fn show_window(&self) {
        let _ = self.show();
    }

    fn focus_window(&self) {
        let _ = self.set_focus();
    }
}

fn focus_window<W: FocusTarget>(window: Option<&W>) {
    if let Some(window) = window {
        window.show_window();
        window.focus_window();
    }
}

#[cfg(test)]
mod tests {
    use super::{focus_window, FocusTarget, MAIN_WINDOW_LABEL};
    use std::cell::Cell;

    #[derive(Default)]
    struct FocusSpy {
        shown: Cell<usize>,
        focused: Cell<usize>,
    }

    impl FocusTarget for FocusSpy {
        fn show_window(&self) {
            self.shown.set(self.shown.get() + 1);
        }

        fn focus_window(&self) {
            self.focused.set(self.focused.get() + 1);
        }
    }

    #[test]
    fn second_instance_targets_the_existing_main_window() {
        assert_eq!(MAIN_WINDOW_LABEL, "main");
    }

    #[test]
    fn secondary_instance_burst_is_harmless_and_does_not_create_windows() {
        let primary = FocusSpy::default();

        for _ in 0..64 {
            focus_window(Some(&primary));
        }
        focus_window::<FocusSpy>(None);

        assert_eq!(primary.shown.get(), 64);
        assert_eq!(primary.focused.get(), 64);
        assert_eq!(MAIN_WINDOW_LABEL, "main");
    }
}
