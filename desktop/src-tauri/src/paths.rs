use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use tauri::{AppHandle, Manager};

const APP_DIRECTORY: &str = "Codex Flow";
const LOG_DIRECTORY: &str = "logs";
const DATABASE_FILE: &str = "codex-flow.sqlite3";

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AppDataPaths {
    pub root: PathBuf,
    pub db_path: PathBuf,
    pub log_dir: PathBuf,
}

pub fn child_paths(app_data_dir: &Path) -> AppDataPaths {
    let root = app_data_dir.join(APP_DIRECTORY);
    AppDataPaths {
        db_path: root.join(DATABASE_FILE),
        log_dir: root.join(LOG_DIRECTORY),
        root,
    }
}

pub fn prepare_paths(app_data_dir: &Path) -> io::Result<AppDataPaths> {
    let paths = child_paths(app_data_dir);
    fs::create_dir_all(&paths.log_dir)?;
    let normalized_root = fs::canonicalize(&paths.root)?;
    Ok(AppDataPaths {
        db_path: normalized_root.join(DATABASE_FILE),
        log_dir: normalized_root.join(LOG_DIRECTORY),
        root: normalized_root,
    })
}

pub fn resolve_runtime_paths(app: &AppHandle) -> tauri::Result<AppDataPaths> {
    let app_data_dir = app.path().app_data_dir()?;
    prepare_paths(&app_data_dir).map_err(Into::into)
}

#[cfg(test)]
mod tests {
    use super::{child_paths, prepare_paths};
    use std::path::Path;

    #[test]
    fn child_names_are_deterministic_for_spaces_and_non_ascii() {
        let paths = child_paths(Path::new(r"C:\Users\测试 User\AppData"));

        assert_eq!(
            paths.root,
            Path::new(r"C:\Users\测试 User\AppData\Codex Flow")
        );
        assert_eq!(
            paths.db_path,
            Path::new(r"C:\Users\测试 User\AppData\Codex Flow\codex-flow.sqlite3")
        );
        assert_eq!(
            paths.log_dir,
            Path::new(r"C:\Users\测试 User\AppData\Codex Flow\logs")
        );
    }

    #[test]
    fn preparation_normalizes_existing_app_data_paths() {
        let base = std::env::temp_dir().join("codex-flow-path-test");
        let paths = prepare_paths(&base).expect("app-data paths");

        assert!(paths.root.is_absolute());
        assert!(paths.root.ends_with("Codex Flow"));
        assert!(paths.db_path.ends_with(r"Codex Flow\codex-flow.sqlite3"));
        assert!(paths.log_dir.ends_with(r"Codex Flow\logs"));
    }
}
