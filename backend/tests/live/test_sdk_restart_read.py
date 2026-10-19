import pytest

from codex_flow.codex_adapter.models import CodexExecutionConfig
from codex_flow.codex_adapter.sdk import SdkCodexAdapter


@pytest.mark.live_codex
async def test_fresh_sdk_adapter_reads_existing_thread_without_starting_a_turn(tmp_path) -> None:
    first = SdkCodexAdapter()
    try:
        thread = await first.create_thread(CodexExecutionConfig(cwd=str(tmp_path)))
        turn = await first.start_turn(thread, "Reply with exactly READY, then stop.")
        events = [event async for event in first.stream_turn(turn)]
        assert events[-1].event_type.value == "TURN_COMPLETED"
    finally:
        await first.close()

    restarted = SdkCodexAdapter()
    try:
        snapshot = await restarted.read_thread(thread)
        assert snapshot.thread.thread_id == thread.thread_id
        assert restarted._turns == {}
    finally:
        await restarted.close()
