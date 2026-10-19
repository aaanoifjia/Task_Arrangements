import pytest

from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.domain.models import ExecutionMode, TaskDefinition
from codex_flow.domain.status import TaskStatus
from codex_flow.scheduler.continuation import (
    ContinuationError,
    ContinuationSource,
    ThreadContinuation,
)


def continuation_task() -> TaskDefinition:
    return TaskDefinition(
        id="child",
        name="Child",
        prompt="continue",
        cwd=".",
        execution_mode=ExecutionMode.CONTINUE_THREAD,
        continue_from_task_id="parent",
    )


async def test_continuation_resumes_source_thread_and_creates_a_new_turn() -> None:
    adapter = FakeCodexAdapter()
    continuation = ThreadContinuation(adapter)
    source = ContinuationSource("parent", TaskStatus.SUCCESS, "fake-thread-7", False)

    result = await continuation.continue_task(continuation_task(), {"parent": source})

    assert result.thread.thread_id == "fake-thread-7"
    assert result.turn.thread_id == "fake-thread-7"
    assert result.turn.turn_id == "fake-turn-1"
    assert adapter.calls == ["resume_thread", "start_turn"]


@pytest.mark.parametrize(
    "source",
    [
        ContinuationSource("parent", TaskStatus.FAILED, "thread", False),
        ContinuationSource("parent", TaskStatus.SUCCESS, None, False),
        ContinuationSource("parent", TaskStatus.SUCCESS, "thread", True),
    ],
)
async def test_continuation_rejects_unsafe_sources(source: ContinuationSource) -> None:
    continuation = ThreadContinuation(FakeCodexAdapter())

    with pytest.raises(ContinuationError):
        await continuation.continue_task(continuation_task(), {"parent": source})


async def test_continuation_requires_an_existing_source() -> None:
    continuation = ThreadContinuation(FakeCodexAdapter())

    with pytest.raises(ContinuationError, match="does not exist"):
        await continuation.continue_task(continuation_task(), {})
