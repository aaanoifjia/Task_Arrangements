use std::io;
use std::process::Command;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum OpenExternalError {
    InvalidScheme,
    MissingThreadId,
    UnsafeUri,
}

pub fn validate_codex_thread_uri(uri: &str) -> Result<(), OpenExternalError> {
    let Some(thread_id) = uri.strip_prefix("codex://threads/") else {
        return Err(OpenExternalError::InvalidScheme);
    };
    if thread_id.is_empty() {
        return Err(OpenExternalError::MissingThreadId);
    }
    if thread_id.contains(['/', '?', '#', '\\']) {
        return Err(OpenExternalError::UnsafeUri);
    }
    Ok(())
}

pub fn open_codex_thread(uri: &str) -> io::Result<()> {
    validate_codex_thread_uri(uri)
        .map_err(|error| io::Error::new(io::ErrorKind::InvalidInput, format!("invalid Codex URI: {error:?}")))?;

    #[cfg(target_os = "windows")]
    let mut command = Command::new("explorer.exe");
    #[cfg(target_os = "macos")]
    let mut command = Command::new("open");
    #[cfg(all(unix, not(target_os = "macos")))]
    let mut command = Command::new("xdg-open");

    command.arg(uri).spawn().map(|_| ())
}

#[tauri::command]
pub fn open_external(uri: String) -> Result<(), String> {
    open_codex_thread(&uri).map_err(|error| error.to_string())
}

#[cfg(test)]
mod tests {
    use super::{validate_codex_thread_uri, OpenExternalError};

    #[test]
    fn accepts_only_codex_thread_uris() {
        assert_eq!(validate_codex_thread_uri("codex://threads/thread-1"), Ok(()));
        assert_eq!(
            validate_codex_thread_uri("https://example.test/thread-1"),
            Err(OpenExternalError::InvalidScheme)
        );
        assert_eq!(
            validate_codex_thread_uri("codex://threads/"),
            Err(OpenExternalError::MissingThreadId)
        );
        assert_eq!(
            validate_codex_thread_uri("codex://threads/thread/child"),
            Err(OpenExternalError::UnsafeUri)
        );
    }
}
