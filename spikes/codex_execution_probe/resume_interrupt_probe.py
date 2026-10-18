import asyncio
import json
from pathlib import Path

from openai_codex import AsyncCodex, CodexConfig, Sandbox


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / "resume_interrupt.json"
CONTROL = ROOT / "workspaces" / "control"


def codex_config():
    # The bundled runtime requires an explicit home directory in this probe's
    # restricted process environment.
    home = str(CONTROL / ".codex-home")
    Path(home).mkdir(parents=True, exist_ok=True)
    return CodexConfig(
        env={
            "HOME": home,
            "CODEX_HOME": home,
            "USERPROFILE": home,
            "HOMEDRIVE": home[:2],
            "HOMEPATH": home[2:],
        }
    )


def status_value(payload):
    turn = getattr(payload, "turn", None)
    status = getattr(turn, "status", None)
    return getattr(status, "value", status)


async def consume(turn, interrupt_after_started=False):
    methods = []
    statuses = []
    response_parts = []
    started = False
    interrupt_requested = False
    interrupt_event_received = False
    terminal_status = None

    async for event in turn.stream():
        methods.append(event.method)
        payload = event.payload
        status = status_value(payload)
        if status is not None:
            statuses.append(status)
        if event.method in ("turn/started", "turn/startedNotification"):
            started = True
            if interrupt_after_started and not interrupt_requested:
                await turn.interrupt()
                interrupt_requested = True
        item = getattr(payload, "item", None)
        text = getattr(item, "text", None)
        if isinstance(text, str):
            response_parts.append(text)
        if event.method == "turn/completed":
            terminal_status = status
            interrupt_event_received = terminal_status == "interrupted"

    return {
        "methods": methods,
        "statuses": statuses,
        "response": "".join(response_parts),
        "started": started,
        "interrupt_requested": interrupt_requested,
        "interrupt_event_received": interrupt_event_received,
        "terminal_status": terminal_status,
    }


async def main():
    CONTROL.mkdir(parents=True, exist_ok=True)
    resume_dir = CONTROL / "resume"
    interrupt_dir = CONTROL / "interrupt"
    resume_dir.mkdir(parents=True, exist_ok=True)
    interrupt_dir.mkdir(parents=True, exist_ok=True)
    result = {"resume": {}, "interrupt": {}}

    try:
        async with AsyncCodex(config=codex_config()) as codex:
            thread = await codex.thread_start(cwd=str(resume_dir), sandbox=Sandbox.workspace_write)
            result["resume"]["thread_id"] = thread.id
            first = await thread.turn("""Remember this exact marker for this thread:

CODEX_FLOW_RESUME_MARKER_7F31

Reply only with:
ACK""")
            result["resume"]["first_turn_id"] = first.id
            first_info = await consume(first)
            result["resume"]["first_terminal_status"] = first_info["terminal_status"]

        async with AsyncCodex(config=codex_config()) as codex:
            thread = await codex.thread_resume(result["resume"]["thread_id"])
            second = await thread.turn("Reply with only the exact marker I told you to remember earlier in this thread.")
            result["resume"]["second_turn_id"] = second.id
            second_info = await consume(second)
            result["resume"]["second_response"] = second_info["response"]
            result["resume"]["resume_verified"] = "CODEX_FLOW_RESUME_MARKER_7F31" in second_info["response"]

            interrupt_thread = await codex.thread_start(cwd=str(interrupt_dir), sandbox=Sandbox.workspace_write)
            interrupt_turn = await interrupt_thread.turn("""Count from 1 to 100000, one integer per line.
Do not summarize.
Do not skip numbers.""")
            result["interrupt"]["thread_id"] = interrupt_thread.id
            result["interrupt"]["turn_id"] = interrupt_turn.id
            interrupt_info = await consume(interrupt_turn, interrupt_after_started=True)
            result["interrupt"]["interrupt_requested"] = interrupt_info["interrupt_requested"]
            result["interrupt"]["interrupt_event_received"] = interrupt_info["interrupt_event_received"]
            result["interrupt"]["interrupt_terminal_status"] = interrupt_info["terminal_status"]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ok = (
        result.get("resume", {}).get("resume_verified") is True
        and result.get("interrupt", {}).get("interrupt_requested") is True
        and result.get("interrupt", {}).get("interrupt_event_received") is True
        and result.get("interrupt", {}).get("interrupt_terminal_status") == "interrupted"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
