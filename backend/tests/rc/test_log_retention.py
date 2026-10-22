"""Release-candidate checks for bounded, scoped server log retention."""

from pathlib import Path

from codex_flow.server import (
    LOG_BACKUP_COUNT,
    LOG_FILE_NAME,
    LOG_MAX_BYTES,
    configure_logging,
)


def test_log_retention_is_bounded_and_preserves_non_codex_flow_files(tmp_path: Path) -> None:
    unrelated = tmp_path / "keep-me.txt"
    unrelated.write_text("do not remove", encoding="utf-8")
    logger = configure_logging(tmp_path)
    payload = "x" * (LOG_MAX_BYTES // 8)

    for sequence in range((LOG_BACKUP_COUNT + 2) * 10):
        logger.info("retention-record=%d %s", sequence, payload)
    for handler in logger.handlers:
        handler.flush()

    retained = sorted(tmp_path.glob(f"{LOG_FILE_NAME}*"))
    assert (tmp_path / LOG_FILE_NAME).exists()
    assert len(retained) <= LOG_BACKUP_COUNT + 1
    assert all(path.stat().st_size <= LOG_MAX_BYTES for path in retained)
    assert not (tmp_path / f"{LOG_FILE_NAME}.{LOG_BACKUP_COUNT + 1}").exists()
    assert unrelated.read_text(encoding="utf-8") == "do not remove"
