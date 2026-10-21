use super::prepare_paths;
use crate::sidecar::{command_arguments, runtime_paths_with_executable};
use std::path::PathBuf;

#[test]
fn repeated_preparation_reuses_the_same_sqlite_path() {
    let base = std::env::temp_dir().join("codex-flow-persistence-test");
    let first = prepare_paths(&base).expect("first app-data path");
    let second = prepare_paths(&base).expect("second app-data path");

    assert_eq!(first.db_path, second.db_path);
    assert_eq!(first.root, second.root);
    assert!(first.db_path.ends_with(r"Codex Flow\codex-flow.sqlite3"));
}

#[test]
fn sidecar_command_uses_the_app_data_database_path() {
    let base = std::env::temp_dir().join("codex-flow-command-test 用户");
    let paths = runtime_paths_with_executable(&base, PathBuf::from("sidecar.exe"))
        .expect("runtime paths");
    let expected = paths.db_path.clone();
    let arguments = command_arguments(&paths, "token");
    let arguments = arguments
        .iter()
        .map(|argument| argument.to_string_lossy().to_string())
        .collect::<Vec<_>>();

    let db_index = arguments.iter().position(|argument| argument == "--db-path").unwrap();
    assert_eq!(PathBuf::from(&arguments[db_index + 1]), expected);
}
