"""Release-candidate matrix for diagnostic secret redaction."""

from pathlib import Path

from codex_flow.server import LOG_FILE_NAME, configure_logging


def test_startup_api_exception_and_shutdown_logs_redact_sensitive_values(
    tmp_path: Path,
) -> None:
    logger = configure_logging(tmp_path)
    bearer = "bearer-credential-value"
    query_token = "query-credential-value"
    prompt = "deploy the private release prompt"
    api_key = "api-key-credential-value"

    logger.info("server starting host=127.0.0.1")
    logger.info("api request authorization: Bearer %s", bearer)
    logger.warning("token rejection path=/ws/runs/run-1?token=%s", query_token)
    logger.info("prompt=%s", prompt)
    logger.error("api failure api_key=%s", api_key)
    try:
        raise RuntimeError(f"exception password={api_key}")
    except RuntimeError:
        logger.exception("exception while handling request")
    logger.info("server shutdown status=complete")

    for handler in logger.handlers:
        handler.flush()
    content = (tmp_path / LOG_FILE_NAME).read_text(encoding="utf-8")

    assert "server starting" in content
    assert "api failure" in content
    assert "server shutdown" in content
    assert "[REDACTED]" in content
    for secret in (bearer, query_token, prompt, api_key):
        assert secret not in content
