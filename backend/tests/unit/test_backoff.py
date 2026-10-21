import pytest

from codex_flow.runtime.backoff import calculate_backoff, sleep_backoff


@pytest.mark.parametrize(
    ("attempt", "expected"),
    [(1, 1.0), (2, 2.0), (3, 4.0), (4, 8.0), (5, 16.0), (6, 30.0), (100, 30.0)],
)
def test_backoff_sequence_is_deterministic_and_capped(attempt: int, expected: float) -> None:
    assert calculate_backoff(attempt) == expected


def test_backoff_honors_custom_base_and_cap() -> None:
    assert calculate_backoff(1, base_seconds=0.25, max_seconds=0.75) == 0.25
    assert calculate_backoff(2, base_seconds=0.25, max_seconds=0.75) == 0.5
    assert calculate_backoff(3, base_seconds=0.25, max_seconds=0.75) == 0.75


@pytest.mark.parametrize(
    ("attempt", "base_seconds", "max_seconds"),
    [(0, 1.0, 30.0), (1, 0.0, 30.0), (1, 1.0, 0.0)],
)
def test_backoff_rejects_invalid_parameters(
    attempt: int, base_seconds: float, max_seconds: float
) -> None:
    with pytest.raises(ValueError):
        calculate_backoff(attempt, base_seconds=base_seconds, max_seconds=max_seconds)


@pytest.mark.asyncio
async def test_sleep_backoff_uses_injected_sleeper() -> None:
    observed: list[float] = []

    async def sleeper(delay: float) -> None:
        observed.append(delay)

    assert await sleep_backoff(3, base_seconds=0.5, max_seconds=2.0, sleeper=sleeper) == 2.0
    assert observed == [2.0]
