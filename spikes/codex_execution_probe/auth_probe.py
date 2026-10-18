"""Probe the installed Codex SDK and the current local Codex session."""

import json
import os
import platform
import sys
from pathlib import Path

import openai_codex
from openai_codex import Codex


_SENSITIVE_KEY_PARTS = ("token", "secret", "key", "credential")
_RESULT_PATH = Path(__file__).parent / "results" / "auth_probe.json"


def ensure_home_environment() -> str:
    candidates = (
        os.environ.get("USERPROFILE", ""),
        os.environ.get("HOME", ""),
        str(Path.home()),
        os.path.join(os.environ.get("HOMEDRIVE", ""), os.environ.get("HOMEPATH", "")),
    )
    canonical_home = next(
        (candidate for candidate in candidates if candidate and Path(candidate).is_dir()),
        None,
    )
    if canonical_home is None:
        raise RuntimeError("No existing Windows home directory could be identified")
    if not os.environ.get("USERPROFILE"):
        os.environ["USERPROFILE"] = canonical_home
    if not os.environ.get("HOME"):
        os.environ["HOME"] = canonical_home
    return canonical_home


def _sanitize(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_text = str(key)
            if any(part in key_text.lower() for part in _SENSITIVE_KEY_PARTS):
                sanitized[key_text] = "***REDACTED***"
            else:
                sanitized[key_text] = _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    return value


def _to_data(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, (dict, list, tuple)):
        return value
    return str(value)


def main():
    try:
        ensure_home_environment()
        with Codex() as codex:
            account = codex.account(refresh_token=False)
    except Exception:
        print("NO_EXISTING_CODEX_SESSION")
        return 1

    result = {
        "python_version": sys.version,
        "openai_codex_version": openai_codex.__version__,
        "platform": platform.platform(),
        "account_access_ok": True,
        "account": _sanitize(_to_data(account)),
    }
    _RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
