"""Fail-closed classification of explicit retryable runtime signals."""

from enum import Enum

_TRANSIENT_SIGNALS = frozenset(
    {
        "SERVER_BUSY",
        "TRANSPORT_OVERLOAD",
        "TRANSPORT_DISCONNECT",
        "TRANSPORT_RESET",
        "DISCONNECTED",
        "CONNECTION_RESET",
    }
)


def is_transient_error(signal: object) -> bool:
    """Return whether an explicit runtime signal is safe to retry.

    Unknown values and natural-language error messages are deliberately not
    interpreted as transient so retry remains fail-closed.
    """
    if isinstance(signal, Enum):
        signal = signal.value
    if not isinstance(signal, str):
        return False
    normalized = signal.strip().upper().replace("-", "_").replace(" ", "_")
    return normalized in _TRANSIENT_SIGNALS
