"""Deterministic bounded retry backoff primitives."""

import asyncio
from collections.abc import Awaitable, Callable


def calculate_backoff(
    attempt: int, *, base_seconds: float = 1.0, max_seconds: float = 30.0
) -> float:
    """Calculate a bounded exponential delay for a one-based retry attempt."""
    if attempt < 1:
        raise ValueError("attempt must be at least 1")
    if base_seconds <= 0:
        raise ValueError("base_seconds must be positive")
    if max_seconds <= 0:
        raise ValueError("max_seconds must be positive")
    if base_seconds >= max_seconds:
        return max_seconds

    delay = base_seconds
    for _ in range(attempt - 1):
        if delay >= max_seconds:
            return max_seconds
        delay = min(max_seconds, delay * 2)
    return min(max_seconds, delay)


async def sleep_backoff(
    attempt: int,
    *,
    base_seconds: float = 1.0,
    max_seconds: float = 30.0,
    sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> float:
    """Sleep for and return the deterministic delay for a retry attempt."""
    delay = calculate_backoff(
        attempt, base_seconds=base_seconds, max_seconds=max_seconds
    )
    await sleeper(delay)
    return delay
