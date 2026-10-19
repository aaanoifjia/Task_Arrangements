import asyncio

import pytest

from codex_flow.codex_adapter.models import CodexExecutionConfig, EventType
from codex_flow.codex_adapter.sdk import SdkCodexAdapter


async def run(adapter: SdkCodexAdapter, cwd: str, prompt: str):
    thread = await adapter.create_thread(CodexExecutionConfig(cwd=cwd))
    turn = await adapter.start_turn(thread, prompt)
    events = [event async for event in adapter.stream_turn(turn)]
    assert events[-1].event_type is EventType.TURN_COMPLETED
    return thread


@pytest.mark.live_codex
async def test_real_fork_join_uses_parallel_workspaces_then_joins(tmp_path) -> None:
    b_cwd, c_cwd = tmp_path / "b", tmp_path / "c"
    b_cwd.mkdir()
    c_cwd.mkdir()
    adapter = SdkCodexAdapter()
    try:
        await run(adapter, str(tmp_path), "Create A.txt containing exactly A_DONE and no newline. Stop.")
        b_thread, c_thread = await asyncio.gather(
            run(adapter, str(b_cwd), "Create B.txt containing exactly B_DONE and no newline. Stop."),
            run(adapter, str(c_cwd), "Create C.txt containing exactly C_DONE and no newline. Stop."),
        )
        assert b_thread.thread_id != c_thread.thread_id
        await run(adapter, str(tmp_path), "Create D.txt containing exactly D_DONE and no newline. Stop.")
        assert (b_cwd / "B.txt").read_text().strip() == "B_DONE"
        assert (c_cwd / "C.txt").read_text().strip() == "C_DONE"
        assert (tmp_path / "D.txt").read_text().strip() == "D_DONE"
    finally:
        await adapter.close()
