use std::fs;
use std::io;
use std::path::Path;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WindowState {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
    pub maximized: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ScreenBounds {
    pub left: i32,
    pub top: i32,
    pub width: u32,
    pub height: u32,
}

impl Default for ScreenBounds {
    fn default() -> Self {
        Self { left: 0, top: 0, width: 1920, height: 1080 }
    }
}

pub fn clamp(state: WindowState, screen: ScreenBounds) -> WindowState {
    let width = state.width.clamp(320, screen.width.max(320));
    let height = state.height.clamp(240, screen.height.max(240));
    let right = screen.left + screen.width as i32 - width as i32;
    let bottom = screen.top + screen.height as i32 - height as i32;
    WindowState {
        x: state.x.clamp(screen.left, right.max(screen.left)),
        y: state.y.clamp(screen.top, bottom.max(screen.top)),
        width,
        height,
        maximized: state.maximized,
    }
}

pub fn serialize(state: &WindowState) -> String {
    format!(
        r#"{{"x":{},"y":{},"width":{},"height":{},"maximized":{}}}"#,
        state.x, state.y, state.width, state.height, state.maximized
    )
}

pub fn deserialize(value: &str) -> Option<WindowState> {
    Some(WindowState {
        x: number(value, "x")? as i32,
        y: number(value, "y")? as i32,
        width: number(value, "width")?,
        height: number(value, "height")?,
        maximized: boolean(value, "maximized")?,
    })
}

pub fn load(path: &Path) -> io::Result<Option<WindowState>> {
    match fs::read_to_string(path) {
        Ok(value) => Ok(deserialize(&value)),
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(None),
        Err(error) => Err(error),
    }
}

pub fn save(path: &Path, state: &WindowState) -> io::Result<()> {
    fs::write(path, serialize(state))
}

fn number(value: &str, field: &str) -> Option<u32> {
    let marker = format!(r#""{}":"#, field);
    let start = value.find(&marker)? + marker.len();
    let digits = value[start..].split(|character: char| !character.is_ascii_digit()).next()?;
    digits.parse().ok()
}

fn boolean(value: &str, field: &str) -> Option<bool> {
    let marker = format!(r#""{}":"#, field);
    let start = value.find(&marker)? + marker.len();
    if value[start..].starts_with("true") { Some(true) } else if value[start..].starts_with("false") { Some(false) } else { None }
}

#[cfg(test)]
mod tests {
    use super::{clamp, deserialize, serialize, ScreenBounds, WindowState};

    fn state() -> WindowState {
        WindowState { x: 80, y: 90, width: 1440, height: 900, maximized: false }
    }

    #[test]
    fn safe_state_round_trips_without_workflow_data() {
        let encoded = serialize(&state());
        assert_eq!(deserialize(&encoded), Some(state()));
        assert!(!encoded.contains("workflow"));
    }

    #[test]
    fn invalid_offscreen_geometry_is_clamped_to_the_screen() {
        let bounded = clamp(
            WindowState { x: -9000, y: 9000, width: 5000, height: 5000, maximized: true },
            ScreenBounds { left: 0, top: 0, width: 1920, height: 1080 },
        );
        assert_eq!(bounded.x, 0);
        assert_eq!(bounded.y, 0);
        assert_eq!(bounded.width, 1920);
        assert_eq!(bounded.height, 1080);
        assert!(bounded.maximized);
    }
}
