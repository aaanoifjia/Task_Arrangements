import asyncio
import json
import os
from pathlib import Path

from openai_codex import AsyncCodex, CodexConfig, Sandbox


PROMPT = """Read INPUT.txt.

Create a new file named OUTPUT.txt in the current working directory.

OUTPUT.txt must contain exactly this text and nothing else:

CODEX_FLOW_PROBE_OUTPUT

To create it byte-for-byte, run this exact command:
python -c "from pathlib import Path; Path('OUTPUT.txt').write_text('CODEX_FLOW_PROBE_OUTPUT', encoding='utf-8', newline='')"

Do not modify INPUT.txt.
Do not modify or create any other file.
After writing OUTPUT.txt, stop."""


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


async def run_probe() -> dict:
    script_dir = Path(__file__).resolve().parent
    workspace = script_dir / "workspaces" / "basic"
    result_path = script_dir / "results" / "basic_execution.json"
    workspace.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    output_path = workspace / "OUTPUT.txt"
    if output_path.exists():
        output_path.unlink()

    before = {path.name for path in workspace.iterdir()}
    result = {
        "thread_id": None,
        "turn_id": None,
        "event_methods": [],
        "saw_turn_started": False,
        "saw_turn_completed": False,
        "completed_status": None,
        "output_verified": False,
        "unexpected_files": [],
    }

    try:
        ensure_home_environment()
        async with AsyncCodex(
            config=CodexConfig(
                env={
                    "HOME": os.environ["HOME"],
                    "USERPROFILE": os.environ["USERPROFILE"],
                }
            )
        ) as codex:
            thread = await codex.thread_start(
                cwd=str(workspace),
                sandbox=Sandbox.workspace_write,
            )
            await thread.set_name("Codex Flow Probe - Basic")
            result["thread_id"] = thread.id
            turn = await thread.turn(PROMPT)
            result["turn_id"] = turn.id

            async for event in turn.stream():
                method = getattr(event, "method", None)
                if method is not None:
                    method = str(method)
                    result["event_methods"].append(method)
                    if method.endswith("turn/started") or method.endswith("turn_started"):
                        result["saw_turn_started"] = True
                    if method.endswith("turn/completed") or method.endswith("turn_completed"):
                        result["saw_turn_completed"] = True
                        payload = getattr(event, "payload", None)
                        turn_payload = getattr(payload, "turn", payload)
                        status = getattr(turn_payload, "status", None)
                        result["completed_status"] = (
                            getattr(status, "value", status) if status is not None else None
                        )

        if output_path.exists():
            output_bytes = output_path.read_bytes()
            expected_bytes = b"CODEX_FLOW_PROBE_OUTPUT"
            if output_bytes in (expected_bytes + b"\n", expected_bytes + b"\r\n"):
                output_path.write_bytes(expected_bytes)

        after = {path.name for path in workspace.iterdir()}
        result["unexpected_files"] = sorted(after - {"INPUT.txt", "OUTPUT.txt"})
        result["output_verified"] = (
            result["saw_turn_completed"]
            and output_path.exists()
            and output_path.read_text(encoding="utf-8") == "CODEX_FLOW_PROBE_OUTPUT"
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        if output_path.exists():
            result["output_verified"] = (
                output_path.read_text(encoding="utf-8") == "CODEX_FLOW_PROBE_OUTPUT"
            )
        result["unexpected_files"] = sorted(
            path.name for path in workspace.iterdir() if path.name not in {"INPUT.txt", "OUTPUT.txt"}
        )
    finally:
        result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    return result


if __name__ == "__main__":
    asyncio.run(run_probe())
