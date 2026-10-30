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


def test_codex_environment_derives_home_from_windows_drive_and_path() -> None:
    source = {
        "HOMEDRIVE": "D:",
        "HOMEPATH": r"\Users\Smoke",
        "PATH": r"C:\Windows\System32",
    }

    environment = _codex_environment(source)

    assert environment["HOME"] == r"D:\Users\Smoke"
    assert environment["PATH"] == source["PATH"]
    assert environment["HOMEDRIVE"] == source["HOMEDRIVE"]
    assert environment["HOMEPATH"] == source["HOMEPATH"]


def test_codex_environment_rejects_missing_windows_home_information() -> None:
    try:
        _codex_environment({"PATH": r"C:\Windows\System32"})
    except ValueError as error:
        assert str(error) == (
            "Codex requires HOME or a valid USERPROFILE/HOMEDRIVE+HOMEPATH environment"
        )
    else:
        raise AssertionError("missing Windows home information must fail explicitly")


def test_codex_environment_preserves_empty_home_by_deriving_userprofile() -> None:
    environment = _codex_environment({"HOME": "", "USERPROFILE": r"C:\Users\Smoke"})

    assert environment["HOME"] == r"C:\Users\Smoke"


def test_sdk_ignores_informational_app_server_notifications() -> None:
    assert SdkCodexAdapter._event_type("turn/moderationMetadata", object()) is None
    assert SdkCodexAdapter._event_type("thread/tokenUsage/updated", object()) is None
    assert SdkCodexAdapter._event_type("turn/started", object()) is EventType.TURN_STARTED
