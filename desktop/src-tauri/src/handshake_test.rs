#[path = "handshake.rs"]
mod handshake;
#[path = "sidecar.rs"]
mod sidecar;

use std::sync::mpsc;
use std::time::Duration;

#[test]
fn valid_canonical_readiness_line_is_parsed() {
    let readiness = handshake::parse_readiness_line(
        r#"{"event":"ready","version":"0.1.0","port":43127,"pid":7124}"#,
    )
    .expect("valid readiness")
    .expect("ready event");

    assert_eq!(readiness.version, "0.1.0");
    assert_eq!(readiness.port, 43127);
    assert_eq!(readiness.pid, 7124);
}

#[test]
fn malformed_and_invalid_readiness_lines_fail_closed() {
    assert_eq!(
        handshake::parse_readiness_line(r#"{"event":"ready","port":0,"pid":1}"#),
        Err(handshake::HandshakeError::Malformed)
    );
    assert_eq!(
        handshake::parse_readiness_line(
            r#"{"event":"ready","version":"0.1.0","port":0,"pid":1}"#,
        ),
        Err(handshake::HandshakeError::InvalidPort(0))
    );
    assert_eq!(
        handshake::parse_readiness_line("normal log line"),
        Ok(None)
    );
}

#[test]
fn timeout_is_reported_when_no_readiness_line_arrives() {
    let (_sender, receiver) = mpsc::channel();
    assert_eq!(
        handshake::wait_for_readiness(&receiver, Duration::from_millis(1)),
        Err(handshake::HandshakeError::Timeout)
    );
}

#[test]
fn sidecar_wait_ignores_stderr_and_non_handshake_stdout() {
    let (sender, receiver) = mpsc::channel();
    sender
        .send(sidecar::SidecarOutput {
            stream: sidecar::SidecarStream::Stderr,
            line: "warning: starting".to_owned(),
        })
        .expect("send stderr");
    sender
        .send(sidecar::SidecarOutput {
            stream: sidecar::SidecarStream::Stdout,
            line: "ordinary log".to_owned(),
        })
        .expect("send log");
    sender
        .send(sidecar::SidecarOutput {
            stream: sidecar::SidecarStream::Stdout,
            line: r#"{"event":"ready","version":"0.1.0","port":43127,"pid":7124}"#
                .to_owned(),
        })
        .expect("send readiness");

    let readiness = sidecar::wait_for_readiness(&receiver, Duration::from_secs(1))
        .expect("readiness");
    assert_eq!(readiness.port, 43127);
}
