use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::time::{Duration, Instant};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HealthError {
    Timeout,
    Unavailable,
}

const POLL_INTERVAL: Duration = Duration::from_millis(50);
const PROBE_TIMEOUT: Duration = Duration::from_millis(100);

pub fn wait_for_health(port: u16, timeout: Duration) -> Result<(), HealthError> {
    wait_until_ready(timeout, POLL_INTERVAL, || probe_health(port).is_ok())
}

pub fn wait_until_ready<F>(timeout: Duration, interval: Duration, mut probe: F) -> Result<(), HealthError>
where
    F: FnMut() -> bool,
{
    let deadline = Instant::now() + timeout;
    loop {
        if probe() {
            return Ok(());
        }
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return Err(HealthError::Timeout);
        }
        std::thread::sleep(interval.min(remaining));
    }
}

fn probe_health(port: u16) -> Result<(), HealthError> {
    let address = SocketAddr::from(([127, 0, 0, 1], port));
    let mut stream = TcpStream::connect_timeout(&address, PROBE_TIMEOUT)
        .map_err(|_| HealthError::Unavailable)?;
    stream
        .set_read_timeout(Some(PROBE_TIMEOUT))
        .map_err(|_| HealthError::Unavailable)?;
    stream
        .set_write_timeout(Some(PROBE_TIMEOUT))
        .map_err(|_| HealthError::Unavailable)?;
    stream
        .write_all(b"GET /healthz HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
        .map_err(|_| HealthError::Unavailable)?;
    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .map_err(|_| HealthError::Unavailable)?;
    let mut lines = response.lines();
    let status_ok = lines
        .next()
        .is_some_and(|line| line.starts_with("HTTP/1.1 200 ") || line.starts_with("HTTP/1.0 200 "));
    let body = response.split_once("\r\n\r\n").map(|(_, body)| body).unwrap_or_default();
    if status_ok && body.contains("\"status\"") && body.contains("\"ok\"") {
        Ok(())
    } else {
        Err(HealthError::Unavailable)
    }
}

#[cfg(test)]
mod tests {
    use super::{wait_until_ready, HealthError};
    use std::time::Duration;

    #[test]
    fn ready_probe_returns_immediately() {
        let mut probes = 0;
        let result = wait_until_ready(Duration::from_secs(1), Duration::from_millis(1), || {
            probes += 1;
            true
        });

        assert_eq!(result, Ok(()));
        assert_eq!(probes, 1);
    }

    #[test]
    fn delayed_probe_retries_until_ready() {
        let mut probes = 0;
        let result = wait_until_ready(Duration::from_secs(1), Duration::from_millis(1), || {
            probes += 1;
            probes >= 3
        });

        assert_eq!(result, Ok(()));
        assert_eq!(probes, 3);
    }

    #[test]
    fn probe_timeout_is_bounded() {
        let result = wait_until_ready(Duration::from_millis(5), Duration::from_millis(1), || false);

        assert_eq!(result, Err(HealthError::Timeout));
    }
}
