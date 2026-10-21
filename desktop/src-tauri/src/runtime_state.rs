use std::sync::Mutex;

use tauri::ipc::{IpcResponse, InvokeResponseBody};
use tauri::State;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RuntimeState {
    pub base_url: String,
    pub token: String,
}

impl RuntimeState {
    pub fn from_readiness(readiness: &crate::sidecar::handshake::Readiness, token: String) -> Self {
        Self {
            base_url: format!("http://127.0.0.1:{}", readiness.port),
            token,
        }
    }

    fn json(&self) -> String {
        format!(
            r#"{{"baseUrl":"{}","token":"{}"}}"#,
            escape_json(&self.base_url),
            escape_json(&self.token)
        )
    }
}

impl IpcResponse for RuntimeState {
    fn body(self) -> tauri::Result<InvokeResponseBody> {
        Ok(InvokeResponseBody::Json(self.json()))
    }
}

#[derive(Default)]
pub struct RuntimeStateStore {
    state: Mutex<Option<RuntimeState>>,
}

impl RuntimeStateStore {
    pub fn unavailable() -> Self {
        Self::default()
    }

    pub fn ready(state: RuntimeState) -> Self {
        Self {
            state: Mutex::new(Some(state)),
        }
    }

    pub fn current(&self) -> Result<RuntimeState, String> {
        self.state
            .lock()
            .map_err(|_| "backend runtime unavailable".to_owned())?
            .clone()
            .ok_or_else(|| "backend runtime unavailable".to_owned())
    }

    pub fn mark_unavailable(&self) -> Result<(), String> {
        self.state
            .lock()
            .map_err(|_| "backend runtime unavailable".to_owned())?
            .take();
        Ok(())
    }
}

#[tauri::command]
pub fn runtime_state(state: State<'_, RuntimeStateStore>) -> Result<RuntimeState, String> {
    state.current()
}

fn escape_json(value: &str) -> String {
    value
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
}

#[cfg(test)]
mod tests {
    use super::{RuntimeState, RuntimeStateStore};

    #[test]
    fn state_is_unavailable_before_readiness() {
        assert_eq!(
            RuntimeStateStore::default().current(),
            Err("backend runtime unavailable".to_owned())
        );
    }

    #[test]
    fn crashed_runtime_is_marked_unavailable() {
        let store = RuntimeStateStore::ready(RuntimeState {
            base_url: "http://127.0.0.1:43127".to_owned(),
            token: "opaque-session-token".to_owned(),
        });

        store.mark_unavailable().expect("mark unavailable");
        assert_eq!(store.current(), Err("backend runtime unavailable".to_owned()));
    }

    #[test]
    fn ready_state_is_returned_exactly_from_memory() {
        let expected = RuntimeState {
            base_url: "http://127.0.0.1:43127".to_owned(),
            token: "opaque-session-token".to_owned(),
        };
        assert_eq!(RuntimeStateStore::ready(expected.clone()).current(), Ok(expected));
    }

    #[test]
    fn ipc_payload_contains_only_runtime_url_and_token() {
        let state = RuntimeState {
            base_url: "http://127.0.0.1:43127".to_owned(),
            token: "opaque-session-token".to_owned(),
        };
        assert_eq!(
            state.json(),
            r#"{"baseUrl":"http://127.0.0.1:43127","token":"opaque-session-token"}"#
        );
    }
}
