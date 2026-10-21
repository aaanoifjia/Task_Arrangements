use std::sync::mpsc::{Receiver, RecvTimeoutError};
use std::time::{Duration, Instant};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Readiness {
    pub version: String,
    pub port: u16,
    pub pid: u32,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HandshakeError {
    Malformed,
    InvalidPort(u32),
    Timeout,
    StreamClosed,
}

pub fn parse_readiness_line(line: &str) -> Result<Option<Readiness>, HandshakeError> {
    let trimmed = line.trim();
    if !trimmed.starts_with('{') || !trimmed.ends_with('}') {
        return Ok(None);
    }

    let Some(event) = string_field(trimmed, "event") else {
        return Ok(None);
    };
    if event != "ready" {
        return Ok(None);
    }

    let version = string_field(trimmed, "version").ok_or(HandshakeError::Malformed)?;
    let port = number_field(trimmed, "port").ok_or(HandshakeError::Malformed)?;
    let pid = number_field(trimmed, "pid").ok_or(HandshakeError::Malformed)?;
    if !(1..=u16::MAX as u32).contains(&port) {
        return Err(HandshakeError::InvalidPort(port));
    }
    let pid = u32::try_from(pid).map_err(|_| HandshakeError::Malformed)?;

    Ok(Some(Readiness {
        version,
        port: port as u16,
        pid,
    }))
}

pub fn wait_for_readiness(
    receiver: &Receiver<String>,
    timeout: Duration,
) -> Result<Readiness, HandshakeError> {
    let deadline = Instant::now() + timeout;
    loop {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return Err(HandshakeError::Timeout);
        }
        match receiver.recv_timeout(remaining) {
            Ok(line) => match parse_readiness_line(&line)? {
                Some(readiness) => return Ok(readiness),
                None => continue,
            },
            Err(RecvTimeoutError::Timeout) => return Err(HandshakeError::Timeout),
            Err(RecvTimeoutError::Disconnected) => return Err(HandshakeError::StreamClosed),
        }
    }
}

fn string_field(object: &str, field: &str) -> Option<String> {
    let marker = format!("\"{field}\"");
    let value = object.split_once(&marker)?.1.trim_start();
    let value = value.strip_prefix(':')?.trim_start();
    let value = value.strip_prefix('"')?;
    let end = value.find('"')?;
    let content = &value[..end];
    if content.contains('\\') {
        return None;
    }
    Some(content.to_owned())
}

fn number_field(object: &str, field: &str) -> Option<u32> {
    let marker = format!("\"{field}\"");
    let value = object.split_once(&marker).map(|(_, value)| value.trim_start())?;
    let value = value.strip_prefix(':')?.trim_start();
    let end = value
        .find(|character: char| !character.is_ascii_digit())
        .unwrap_or(value.len());
    if end == 0 {
        return None;
    }
    value[..end].parse().ok()
}
