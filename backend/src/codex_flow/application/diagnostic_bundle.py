"""Reproducible, allowlisted diagnostic bundle generation."""

import json
import re
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from codex_flow.application.diagnostics import DiagnosticSummary

BUNDLE_SCHEMA_VERSION = 1
MAX_LOG_BYTES = 64 * 1024
_REDACTION_PATTERNS = (
    re.compile(r"(?i)(\b(?:authorization\s*:\s*bearer|bearer)\s+)[^\s,;]+"),
    re.compile(r"(?i)(\b(?:token|password|secret|api[_-]?key|access[_-]?token)\s*[=:]\s*)[^\s,;&]+"),
    re.compile(r"(?i)(\bprompt\s*[=:]\s*).*$"),
)
_MANIFEST_FIELDS = frozenset({"filename", "kind", "name", "sha256", "size"})


def redact_diagnostic_logs(logs: Iterable[str]) -> str:
    """Redact sensitive log fields and bound the resulting UTF-8 payload."""

    redacted_lines: list[str] = []
    for line in logs:
        redacted = line
        for pattern in _REDACTION_PATTERNS:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        redacted_lines.append(redacted)
    encoded = "\n".join(redacted_lines).encode("utf-8")[:MAX_LOG_BYTES]
    return encoded.decode("utf-8", errors="ignore")


def _safe_manifest(manifest: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: item[key] for key in sorted(_MANIFEST_FIELDS) if key in item}
        for item in manifest
    ]


def _write_entry(bundle: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    bundle.writestr(info, payload)


def create_diagnostic_bundle(
    output_path: Path,
    summary: DiagnosticSummary,
    *,
    logs: Iterable[str] = (),
    artifact_manifest: Sequence[Mapping[str, Any]] | None = None,
) -> Path:
    """Write a reproducible ZIP bundle containing only approved diagnostics."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostic_json = json.dumps(
        summary.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    metadata_json = json.dumps(
        {
            "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
            "backend_version": summary.backend_version,
            "db_schema_version": summary.db_schema_version,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        _write_entry(bundle, "diagnostics/summary.json", diagnostic_json)
        _write_entry(bundle, "diagnostics/metadata.json", metadata_json)
        _write_entry(bundle, "logs/redacted.log", redact_diagnostic_logs(logs).encode("utf-8"))
        if artifact_manifest is not None:
            manifest_json = json.dumps(
                _safe_manifest(artifact_manifest), ensure_ascii=False, separators=(",", ":"), sort_keys=True
            ).encode("utf-8")
            _write_entry(bundle, "artifacts/manifest.json", manifest_json)
    return output_path
