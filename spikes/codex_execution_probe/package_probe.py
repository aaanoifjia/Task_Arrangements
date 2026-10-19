"""Minimal frozen-runtime feasibility probe for the Codex Python SDK."""

import json
import sys
from pathlib import Path

import openai_codex
from openai_codex import Codex


RESULT_PATH = Path(__file__).parent / "results" / "package_probe.json"


def main() -> int:
    result = {
        "sdk_version": openai_codex.__version__,
        "account_access_ok": False,
    }
    try:
        with Codex() as codex:
            codex.account(refresh_token=False)
        result["account_access_ok"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    print(f"sdk_version={result['sdk_version']}")
    print(f"account_access_ok={str(result['account_access_ok']).lower()}")
    if not getattr(sys, "frozen", False):
        RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["account_access_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
