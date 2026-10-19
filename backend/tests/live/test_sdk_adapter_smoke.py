import pytest

from codex_flow.codex_adapter.models import CodexExecutionConfig, EventType
from codex_flow.codex_adapter.sdk import SdkCodexAdapter


@pytest.mark.live_codex
@pytest.mark.asyncio
async def test_sdk_adapter_writes_exact_file(tmp_path) -> None:
    adapter = SdkCodexAdapter()
    try:
        thread = await adapter.create_thread(CodexExecutionConfig(cwd=str(tmp_path)))
        turn = await adapter.start_turn(thread, "Create OUTPUT.txt with exactly SDK_ADAPTER_SMOKE and no newline. Stop.")
        events = [event async for event in adapter.stream_turn(turn)]
        assert events[-1].event_type is EventType.TURN_COMPLETED
        assert (tmp_path / "OUTPUT.txt").read_text(encoding="utf-8").strip() == "SDK_ADAPTER_SMOKE"
    finally:
        await adapter.close()
