use std::collections::VecDeque;
use std::env;
use std::ffi::OsString;
use std::fs;
use std::io::{self, BufRead, BufReader, Read};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread::{self, JoinHandle};
use std::time::{SystemTime, UNIX_EPOCH};

const SIDECAR_BASENAME: &str = "codex-flow-server";
const WINDOWS_TARGET: &str = "x86_64-pc-windows-msvc";

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RuntimePaths {
    pub root: PathBuf,
    pub db_path: PathBuf,
    pub log_dir: PathBuf,
    pub executable: PathBuf,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SidecarStream {
    Stdout,
    Stderr,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SidecarOutput {
    pub stream: SidecarStream,
    pub line: String,
}

pub struct SidecarProcess {
    pub token: String,
    pub output: Receiver<SidecarOutput>,
    child: Child,
    _stdout_thread: JoinHandle<()>,
    _stderr_thread: JoinHandle<()>,
}

impl Drop for SidecarProcess {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

pub fn default_runtime_paths() -> io::Result<RuntimePaths> {
    let local_app_data = env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .or_else(|| {
            env::var_os("USERPROFILE")
                .map(PathBuf::from)
                .map(|path| path.join("AppData").join("Local"))
        })
        .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "local app-data directory missing"))?;
    let root = local_app_data.join("Codex Flow");
    let log_dir = root.join("logs");
    fs::create_dir_all(&log_dir)?;
    Ok(RuntimePaths {
        db_path: root.join("codex-flow.sqlite3"),
        executable: find_sidecar_executable()?,
        log_dir,
        root,
    })
}

fn find_sidecar_executable() -> io::Result<PathBuf> {
    let executable_root = env::current_exe()?
        .parent()
        .map(Path::to_path_buf)
        .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "desktop executable directory missing"))?;
    let candidates = [
        executable_root
            .join("binaries")
            .join(format!("{SIDECAR_BASENAME}-{WINDOWS_TARGET}.exe")),
        executable_root.join("binaries").join(format!("{SIDECAR_BASENAME}.exe")),
        executable_root.join(format!("{SIDECAR_BASENAME}-{WINDOWS_TARGET}.exe")),
        executable_root.join(format!("{SIDECAR_BASENAME}.exe")),
    ];
    candidates
        .into_iter()
        .find(|candidate| candidate.is_file())
        .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "sidecar executable missing"))
}

pub fn generate_session_token() -> String {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    format!("{nanos:032x}-{:08x}", std::process::id())
}

pub fn command_arguments(paths: &RuntimePaths, token: &str) -> Vec<OsString> {
    Vec::from([
        OsString::from("--host"),
        OsString::from("127.0.0.1"),
        OsString::from("--port"),
        OsString::from("0"),
        OsString::from("--db-path"),
        paths.db_path.clone().into_os_string(),
        OsString::from("--token"),
        OsString::from(token),
        OsString::from("--log-dir"),
        paths.log_dir.clone().into_os_string(),
    ])
}

pub fn build_command(paths: &RuntimePaths, token: &str) -> Command {
    let mut command = Command::new(&paths.executable);
    command
        .args(command_arguments(paths, token))
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    command
}

pub fn launch_sidecar(paths: &RuntimePaths) -> io::Result<SidecarProcess> {
    let token = generate_session_token();
    let mut child = build_command(paths, &token).spawn()?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| io::Error::other("sidecar stdout pipe missing"))?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| io::Error::other("sidecar stderr pipe missing"))?;
    let (sender, output) = mpsc::channel();
    let stdout_thread = spawn_output_reader(stdout, SidecarStream::Stdout, sender.clone());
    let stderr_thread = spawn_output_reader(stderr, SidecarStream::Stderr, sender);
    Ok(SidecarProcess {
        token,
        output,
        child,
        _stdout_thread: stdout_thread,
        _stderr_thread: stderr_thread,
    })
}

fn spawn_output_reader<R: Read + Send + 'static>(
    reader: R,
    stream: SidecarStream,
    sender: Sender<SidecarOutput>,
) -> JoinHandle<()> {
    thread::spawn(move || {
        let buffered = BufReader::new(reader);
        for line in buffered.lines().map_while(Result::ok) {
            let _ = sender.send(SidecarOutput {
                stream: stream.clone(),
                line,
            });
        }
    })
}

#[allow(dead_code)]
fn drain_output(receiver: &Receiver<SidecarOutput>) -> VecDeque<SidecarOutput> {
    receiver.try_iter().collect()
}

#[cfg(test)]
mod tests {
    use super::{command_arguments, generate_session_token, RuntimePaths};
    use std::path::PathBuf;

    fn paths() -> RuntimePaths {
        RuntimePaths {
            root: PathBuf::from("C:/Codex Flow"),
            db_path: PathBuf::from("C:/Codex Flow/codex-flow.sqlite3"),
            log_dir: PathBuf::from("C:/Codex Flow/logs"),
            executable: PathBuf::from("C:/Codex Flow/codex-flow-server.exe"),
        }
    }

    #[test]
    fn command_is_loopback_only_and_does_not_request_a_shell() {
        let arguments = command_arguments(&paths(), "test-token");
        let arguments = arguments
            .iter()
            .map(|argument| argument.to_string_lossy().to_string())
            .collect::<Vec<_>>();

        assert!(arguments.windows(2).any(|pair| pair == ["--host", "127.0.0.1"]));
        assert!(arguments.windows(2).any(|pair| pair == ["--port", "0"]));
        assert!(!arguments.iter().any(|argument| argument == "shell=true"));
        assert!(!arguments.iter().any(|argument| argument == "cmd.exe"));
    }

    #[test]
    fn generated_tokens_are_nonempty_and_distinct() {
        let first = generate_session_token();
        let second = generate_session_token();

        assert!(!first.is_empty());
        assert!(!second.is_empty());
        assert_ne!(first, second);
    }
}
