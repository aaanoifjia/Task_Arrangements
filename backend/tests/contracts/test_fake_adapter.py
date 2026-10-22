import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter, FakeScenario
from codex_flow.codex_adapter.models import CodexExecutionConfig, CodexThreadRef, EventType


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", list(FakeScenario))
async def test_fake_stream_is_deterministic(scenario: FakeScenario) -> None:
    adapter = FakeCodexAdapter(scenario)
    thread = await adapter.create_thread(CodexExecutionConfig(cwd="C:/workspace"))
    turn = await adapter.start_turn(thread, "prompt")
    events = [event async for event in adapter.stream_turn(turn)]
    assert thread.thread_id == "fake-thread-1"
    assert turn.turn_id == "fake-turn-1"
    assert next(event.event_type for event in events) is EventType.TURN_STARTED
    assert adapter.calls == ["create_thread", "start_turn", "stream_turn"]


@pytest.mark.asyncio
async def test_fake_resume_interrupt_snapshot_and_close() -> None:
    adapter = FakeCodexAdapter()
    thread = CodexThreadRef(thread_id="fake-thread-1")
    assert await adapter.resume_thread(thread) == thread
    await adapter.set_thread_name(thread, "name")
    assert (await adapter.read_thread(thread)).name == "name"
    turn = await adapter.start_turn(thread, "prompt")
    assert (await adapter.interrupt_turn(turn)).terminal_event is EventType.TURN_INTERRUPTED
    assert [event async for event in adapter.stream_turn(turn)][-1].event_type is EventType.TURN_INTERRUPTED
    await adapter.close()
    await adapter.close()
