import asyncio

import pytest

from codex_flow.scheduler.locks import (
    GlobalConcurrencyLimiter,
    ThreadTurnLockManager,
    WorkspaceLockManager,
    canonical_workspace_key,
)


async def hold_workspace(manager: WorkspaceLockManager, key: str, entered: asyncio.Event, release: asyncio.Event) -> None:
    async with manager.acquire_write(key):
        entered.set()
        await release.wait()


@pytest.mark.asyncio
async def test_workspace_same_key_serializes_and_releases() -> None:
    manager = WorkspaceLockManager()
    entered = asyncio.Event()
    release = asyncio.Event()
    first = asyncio.create_task(hold_workspace(manager, r"C:\Work\Project", entered, release))
    await entered.wait()
    second_entered = asyncio.Event()
    second = asyncio.create_task(hold_workspace(manager, r"c:\work\project", second_entered, release))
    await asyncio.sleep(0)
    assert not second_entered.is_set()
    release.set()
    await asyncio.gather(first, second)
    assert second_entered.is_set()


@pytest.mark.asyncio
async def test_workspace_different_keys_can_proceed() -> None:
    manager = WorkspaceLockManager()
    one_entered = asyncio.Event()
    two_entered = asyncio.Event()
    release = asyncio.Event()
    tasks = asyncio.gather(
        hold_workspace(manager, "one", one_entered, release),
        hold_workspace(manager, "two", two_entered, release),
    )
    await asyncio.wait_for(asyncio.gather(one_entered.wait(), two_entered.wait()), timeout=1)
    release.set()
    await tasks


def test_canonical_key_is_case_insensitive() -> None:
    assert canonical_workspace_key(r"C:\Work\Project") == canonical_workspace_key(r"c:\work\project")


@pytest.mark.asyncio
async def test_global_limiter_and_exception_release() -> None:
    with pytest.raises(ValueError):
        GlobalConcurrencyLimiter(0)
    limiter = GlobalConcurrencyLimiter(1)
    entered = asyncio.Event()
    release = asyncio.Event()

    async def first() -> None:
        async with limiter.slot():
            entered.set()
            await release.wait()

    task = asyncio.create_task(first())
    await entered.wait()
    blocked_context = limiter.slot()
    blocked = asyncio.create_task(blocked_context.__aenter__())
    await asyncio.sleep(0)
    assert not blocked.done()
    release.set()
    await task
    await blocked
    await blocked_context.__aexit__(None, None, None)
    with pytest.raises(RuntimeError):
        async with limiter.slot():
            raise RuntimeError
    context = limiter.slot()
    await context.__aenter__()
    await context.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_global_limit_two_allows_two_holders() -> None:
    limiter = GlobalConcurrencyLimiter(2)
    entered = asyncio.Event()
    release = asyncio.Event()
    count = 0

    async def holder() -> None:
        nonlocal count
        async with limiter.slot():
            count += 1
            if count == 2:
                entered.set()
            await release.wait()

    tasks = [asyncio.create_task(holder()), asyncio.create_task(holder())]
    await asyncio.wait_for(entered.wait(), timeout=1)
    release.set()
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_workspace_and_thread_locks_release_after_exception() -> None:
    workspace = WorkspaceLockManager()
    with pytest.raises(RuntimeError):
        async with workspace.acquire_write("workspace"):
            raise RuntimeError
    async with workspace.acquire_write("workspace"):
        pass

    threads = ThreadTurnLockManager()
    with pytest.raises(RuntimeError):
        async with threads.acquire_turn("thread"):
            raise RuntimeError
    async with threads.acquire_turn("thread"):
        pass


@pytest.mark.asyncio
async def test_thread_turn_lock_same_serializes_different_parallel() -> None:
    manager = ThreadTurnLockManager()
    async with manager.acquire_turn("same"):
        waiting_context = manager.acquire_turn("same")
        waiting = asyncio.create_task(waiting_context.__aenter__())
        await asyncio.sleep(0)
        assert not waiting.done()
    await waiting
    await waiting_context.__aexit__(None, None, None)

    entered_one = asyncio.Event()
    entered_two = asyncio.Event()
    release = asyncio.Event()

    async def holder(thread_id: str, entered: asyncio.Event) -> None:
        async with manager.acquire_turn(thread_id):
            entered.set()
            await release.wait()

    tasks = [
        asyncio.create_task(holder("one", entered_one)),
        asyncio.create_task(holder("two", entered_two)),
    ]
    await asyncio.wait_for(asyncio.gather(entered_one.wait(), entered_two.wait()), timeout=1)
    release.set()
    await asyncio.gather(*tasks)
