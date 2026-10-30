from codex_flow.codex_adapter.models import EventType
from codex_flow.codex_adapter.sdk import SdkCodexAdapter, _codex_environment


def test_codex_environment_derives_home_from_windows_userprofile() -> None:
    environment = _codex_environment(
        {"USERPROFILE": r"C:\Users\Smoke", "HOMEDRIVE": "C:", "HOMEPATH": r"\Users\Smoke"}
    )

    assert environment["HOME"] == r"C:\Users\Smoke"


def test_codex_environment_preserves_existing_home() -> None:
    environment = _codex_environment({"HOME": r"D:\Existing", "USERPROFILE": r"C:\Users\Smoke"})

    assert environment["HOME"] == r"D:\Existing"


def test_sdk_ignores_informational_app_server_notifications() -> None:
    assert SdkCodexAdapter._event_type("turn/moderationMetadata", object()) is None
    assert SdkCodexAdapter._event_type("thread/tokenUsage/updated", object()) is None
    assert SdkCodexAdapter._event_type("turn/started", object()) is EventType.TURN_STARTED
