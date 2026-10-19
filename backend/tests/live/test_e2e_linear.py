import pytest

from codex_flow.codex_adapter.models import CodexExecutionConfig, EventType
from codex_flow.codex_adapter.sdk import SdkCodexAdapter


@pytest.mark.live_codex
async def test_real_linear_dependency_creates_b_after_a_terminal(tmp_path) -> None:
    adapter = SdkCodexAdapter()
    try:
        task_a = await adapter.create_thread(CodexExecutionConfig(cwd=str(tmp_path)))
        turn_a = await adapter.start_turn(task_a, "Create A.txt containing exactly A_DONE and no newline. Stop.")
        events_a = [event async for event in adapter.stream_turn(turn_a)]
        assert events_a[-1].event_type is EventType.TURN_COMPLETED
        assert (tmp_path / "A.txt").read_text(encoding="utf-8").strip() == "A_DONE"

        task_b = await adapter.create_thread(CodexExecutionConfig(cwd=str(tmp_path)))
        assert task_b.thread_id != task_a.thread_id
        turn_b = await adapter.start_turn(
            task_b,
            "Verify A.txt contains A_DONE. Create B.txt containing exactly B_DONE and no newline. Stop.",
        )
        events_b = [event async for event in adapter.stream_turn(turn_b)]
        assert events_b[-1].event_type is EventType.TURN_COMPLETED
        assert (tmp_path / "B.txt").read_text(encoding="utf-8").strip() == "B_DONE"
    finally:
        await adapter.close()
