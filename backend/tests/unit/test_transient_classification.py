from enum import StrEnum

import pytest

from codex_flow.runtime.transient import is_transient_error


class Signal(StrEnum):
    SERVER_BUSY = "SERVER_BUSY"
    TRANSPORT_DISCONNECT = "TRANSPORT_DISCONNECT"


@pytest.mark.parametrize(
    ("signal", "expected"),
    [
        ("SERVER_BUSY", True),
        ("transport-overload", True),
        ("transport disconnect", True),
        ("TRANSPORT_RESET", True),
        (Signal.SERVER_BUSY, True),
        ("TASK_FAILED", False),
        ("PERMISSION_DENIED", False),
        ("INVALID_PROMPT", False),
        ("INTERRUPTED", False),
        ("TRANSPORT_ERROR", False),
        ("server busy because the task failed", False),
        (None, False),
        (object(), False),
    ],
)
def test_transient_classification_is_explicit_and_fail_closed(
    signal: object, expected: bool
) -> None:
    assert is_transient_error(signal) is expected
