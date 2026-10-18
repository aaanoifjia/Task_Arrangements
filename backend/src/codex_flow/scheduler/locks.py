import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path


def canonical_workspace_key(cwd: str) -> str:
    return str(Path(cwd).absolute().resolve(strict=False)).casefold()


class WorkspaceLockManager:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def _get_lock(self, cwd: str) -> asyncio.Lock:
        key = canonical_workspace_key(cwd)
        async with self._lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    @asynccontextmanager
    async def acquire_write(self, cwd: str) -> AsyncIterator[None]:
        lock = await self._get_lock(cwd)
        async with lock:
            yield


class GlobalConcurrencyLimiter:
    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        self._semaphore = asyncio.Semaphore(limit)

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        async with self._semaphore:
            yield


class ThreadTurnLockManager:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def _get_lock(self, thread_id: str) -> asyncio.Lock:
        async with self._lock:
            if thread_id not in self._locks:
                self._locks[thread_id] = asyncio.Lock()
            return self._locks[thread_id]

    @asynccontextmanager
    async def acquire_turn(self, thread_id: str) -> AsyncIterator[None]:
        lock = await self._get_lock(thread_id)
        async with lock:
            yield
