use std::collections::VecDeque;
use std::env;
use std::ffi::OsString;
use std::io::{self, BufRead, BufReader, Read};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread::{self, JoinHandle};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

#[path = "handshake.rs"]
pub mod handshake;
#[path = "health.rs"]
pub mod health;
#[cfg(test)]
#[path = "sidecar_test.rs"]
mod sidecar_test;

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
    paths: RuntimePaths,
    relaunch_count: u8,
    child: Child,
    _stdout_thread: JoinHandle<()>,
    _stderr_thread: JoinHandle<()>,
}

impl Drop for SidecarProcess {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}

impl SidecarProcess {
    pub fn poll_exit(&mut self) -> io::Result<Option<std::process::ExitStatus>> {
        self.child.try_wait()
    }

    pub fn shutdown(&mut self) -> io::Result<()> {
        if self.child.try_wait()?.is_some() {
            return Ok(());
        }
        self.child.kill()?;
        self.child.wait().map(|_| ())
    }

    pub fn relaunch(&mut self) -> io::Result<()> {
        if self.relaunch_count >= 1 {
            return Err(io::Error::new(
                io::ErrorKind::AlreadyExists,
                "sidecar relaunch limit reached",
            ));
        }

        self.shutdown()?;
        let token = generate_session_token();
        let mut child = build_command(&self.paths, &token).spawn()?;
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
        self.token = token;
        self.output = output;
        self.child = child;
        self._stdout_thread = stdout_thread;
        self._stderr_thread = stderr_thread;
        self.relaunch_count += 1;
        Ok(())
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
    runtime_paths_from_app_data(&local_app_data)
}

pub fn runtime_paths_from_app_data(app_data_dir: &Path) -> io::Result<RuntimePaths> {
    runtime_paths_with_executable(app_data_dir, find_sidecar_executable()?)
}

pub fn runtime_paths_with_executable(
    app_data_dir: &Path,
    executable: PathBuf,
) -> io::Result<RuntimePaths> {
    let app_paths = crate::paths::prepare_paths(app_data_dir)?;
    Ok(RuntimePaths {
        db_path: app_paths.db_path,
        executable,
        log_dir: app_paths.log_dir,
        root: app_paths.root,
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
    preserve_codex_environment(&mut command);
    command
}

pub fn preserve_codex_environment(command: &mut Command) {
    for key in ["HOME", "USERPROFILE", "PATH"] {
        if let Some(value) = env::var_os(key) {
            command.env(key, value);
        }
    }
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
        paths: paths.clone(),
        relaunch_count: 0,
        child,
        _stdout_thread: stdout_thread,
        _stderr_thread: stderr_thread,
    })
}

pub fn wait_for_readiness(
    receiver: &Receiver<SidecarOutput>,
    timeout: std::time::Duration,
) -> Result<handshake::Readiness, handshake::HandshakeError> {
    let deadline = Instant::now() + timeout;
    loop {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return Err(handshake::HandshakeError::Timeout);
        }
        match receiver.recv_timeout(remaining) {
            Ok(output) if output.stream == SidecarStream::Stdout => {
                match handshake::parse_readiness_line(&output.line)? {
                Some(readiness) => {
                    health::wait_for_health(readiness.port, timeout).map_err(|error| match error {
                        health::HealthError::Timeout => handshake::HandshakeError::Timeout,
                        health::HealthError::Unavailable => handshake::HandshakeError::StreamClosed,
                    })?;
                    return Ok(readiness);
                }
                    None => continue,
                }
            }
            Ok(_) => continue,
            Err(mpsc::RecvTimeoutError::Timeout) => {
                return Err(handshake::HandshakeError::Timeout)
            }
            Err(mpsc::RecvTimeoutError::Disconnected) => {
                return Err(handshake::HandshakeError::StreamClosed)
            }
        }
    }
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
    use super::{command_arguments, generate_session_token, RuntimePaths, SidecarProcess};
    use std::process::Command;
    use std::path::PathBuf;
    use std::sync::mpsc;
    use std::thread;

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

    #[test]
    fn shutdown_is_idempotent_for_an_already_exited_child() {
        let child = Command::new("cmd.exe")
            .args(["/C", "exit", "0"])
            .spawn()
            .expect("spawn test child");
        let (sender, output) = mpsc::channel();
        drop(sender);
        let mut process = SidecarProcess {
            token: "test-token".to_owned(),
            output,
            paths: paths(),
            relaunch_count: 0,
            child,
            _stdout_thread: thread::spawn(|| {}),
            _stderr_thread: thread::spawn(|| {}),
        };

        process.shutdown().expect("first shutdown");
        process.shutdown().expect("second shutdown");
        assert_eq!(process.output.try_iter().count(), 0);
    }

    #[test]
    fn unexpected_child_exit_is_observable_without_silently_restarting() {
        let child = Command::new("cmd.exe")
            .args(["/C", "exit", "7"])
            .spawn()
            .expect("spawn test child");
        let (_sender, output) = mpsc::channel();
        let mut process = SidecarProcess {
            token: "test-token".to_owned(),
            output,
            paths: paths(),
            relaunch_count: 0,
            child,
            _stdout_thread: thread::spawn(|| {}),
            _stderr_thread: thread::spawn(|| {}),
        };

        let mut exit = None;
        for _ in 0..100 {
            exit = process.poll_exit().expect("poll child");
            if exit.is_some() {
                break;
            }
            thread::sleep(std::time::Duration::from_millis(1));
        }
        assert_eq!(exit.expect("child exit").code(), Some(7));
    }

    #[test]
    fn relaunch_reuses_paths_refreshes_token_and_stops_after_one_attempt() {
        let paths = RuntimePaths {
            root: PathBuf::from("C:/Codex Flow"),
            db_path: PathBuf::from("C:/Codex Flow/codex-flow.sqlite3"),
            log_dir: PathBuf::from("C:/Codex Flow/logs"),
            executable: PathBuf::from("cmd.exe"),
        };
        let mut process = super::launch_sidecar(&paths).expect("launch test sidecar");
        let original_token = process.token.clone();
        process.relaunch().expect("first relaunch");

        assert_ne!(process.token, original_token);
        assert_eq!(process.paths.db_path, paths.db_path);
        assert_eq!(
            process.relaunch().expect_err("second relaunch must be blocked").kind(),
            std::io::ErrorKind::AlreadyExists
        );
    }

    #[test]
    fn launched_process_retains_app_data_paths_and_auth_token_contract() {
        let paths = paths();
        let token = "integration-session-token";
        let command = super::build_command(&paths, token);
        let arguments = command
            .get_args()
            .map(|argument| argument.to_string_lossy().to_string())
            .collect::<Vec<_>>();
        let db_path = paths.db_path.to_string_lossy().to_string();
        let log_dir = paths.log_dir.to_string_lossy().to_string();

        assert!(arguments.windows(2).any(|pair| pair == ["--db-path", &db_path]));
        assert!(arguments.windows(2).any(|pair| pair == ["--log-dir", &log_dir]));
        assert!(arguments.windows(2).any(|pair| pair == ["--token", token]));
        assert_eq!(arguments[1], "127.0.0.1");
    }

    #[test]
    fn crashed_process_is_observable_before_bounded_relaunch() {
        let paths = RuntimePaths {
            executable: PathBuf::from("cmd.exe"),
            ..paths()
        };
        let mut process = super::launch_sidecar(&paths).expect("launch test sidecar");
        let original_token = process.token.clone();
        let mut exit = None;
        for _ in 0..100 {
            exit = process.poll_exit().expect("poll child");
            if exit.is_some() {
                break;
            }
            thread::sleep(std::time::Duration::from_millis(1));
        }
        assert!(exit.is_some(), "test sidecar should exit");
        process.relaunch().expect("relaunch once after crash");
        assert_ne!(process.token, original_token);
        assert_eq!(
            process.relaunch().expect_err("relaunch loop must be blocked").kind(),
            std::io::ErrorKind::AlreadyExists
        );
    }
}
