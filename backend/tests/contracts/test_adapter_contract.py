import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.codex_adapter.models import CodexExecutionConfig, EventType


@pytest.mark.asyncio
async def test_adapter_contract_with_fake() -> None:
    adapter = FakeCodexAdapter()
    thread = await adapter.create_thread(CodexExecutionConfig(cwd="C:/workspace"))
    assert thread.thread_id
    turn = await adapter.start_turn(thread, "prompt")
    assert turn.turn_id
    events = [event async for event in adapter.stream_turn(turn)]
    assert events[0].event_type is EventType.TURN_STARTED
    assert events[-1].event_type is EventType.TURN_COMPLETED
    assert await adapter.resume_thread(thread) == thread
    assert (await adapter.interrupt_turn(turn)).terminal_event is EventType.TURN_INTERRUPTED
    assert [event async for event in adapter.stream_turn(turn)][-1].event_type is EventType.TURN_INTERRUPTED
    await adapter.set_thread_name(thread, "contract")
    assert (await adapter.read_thread(thread)).thread == thread
    await adapter.close()
    await adapter.close()
