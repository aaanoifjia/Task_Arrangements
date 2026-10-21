use super::{build_command, RuntimePaths};
use std::env;
use std::ffi::OsStr;
use std::path::PathBuf;

#[test]
fn command_preserves_auth_home_and_runtime_path() {
    let paths = RuntimePaths {
        root: PathBuf::from(r"C:UsersAdministratorAppDataLocalCodex Flow"),
        db_path: PathBuf::from(r"C:UsersAdministratorAppDataLocalCodex Flowcodex-flow.sqlite3"),
        log_dir: PathBuf::from(r"C:UsersAdministratorAppDataLocalCodex Flowlogs"),
        executable: PathBuf::from(r"C:Codex Flowcodex-flow-server.exe"),
    };
    let command = build_command(&paths, "opaque-token");

    for key in ["HOME", "USERPROFILE", "PATH"] {
        let expected = env::var_os(key);
        if expected.is_none() {
            continue;
        }
        let configured = command
            .get_envs()
            .find(|(name, _)| *name == OsStr::new(key))
            .and_then(|(_, value)| value);
        assert_eq!(configured, expected.as_deref(), "{key} must be inherited");
    }
}

#[test]
fn command_does_not_redirect_auth_home_to_app_data() {
    let paths = RuntimePaths {
        root: PathBuf::from(r"C:UsersAdministratorAppDataLocalCodex Flow"),
        db_path: PathBuf::from(r"C:UsersAdministratorAppDataLocalCodex Flowcodex-flow.sqlite3"),
        log_dir: PathBuf::from(r"C:UsersAdministratorAppDataLocalCodex Flowlogs"),
        executable: PathBuf::from(r"C:Codex Flowcodex-flow-server.exe"),
    };
    let command = build_command(&paths, "opaque-token");

    for key in ["HOME", "USERPROFILE"] {
        let configured = command
            .get_envs()
            .find(|(name, _)| *name == OsStr::new(key))
            .and_then(|(_, value)| value);
        assert_ne!(configured, Some(paths.root.as_os_str()));
    }
}
