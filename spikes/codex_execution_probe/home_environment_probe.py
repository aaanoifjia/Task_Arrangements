import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / "home_environment.json"


def existing_directory(value: str) -> bool:
    return bool(value) and Path(value).is_dir()


def canonical_home() -> tuple[str | None, str]:
    userprofile = os.environ.get("USERPROFILE", "")
    home = os.environ.get("HOME", "")
    path_home = str(Path.home())
    expanduser_home = os.path.expanduser("~")
    drive_home = os.path.join(
        os.environ.get("HOMEDRIVE", ""), os.environ.get("HOMEPATH", "")
    )
    candidates = (
        ("USERPROFILE", userprofile),
        ("HOME", home),
        ("Path.home", path_home),
        ("HOMEDRIVE+HOMEPATH", drive_home),
    )
    selected = next(
        (value for _name, value in candidates if existing_directory(value)),
        None,
    )
    return selected, expanduser_home


def main() -> int:
    values = {
        "HOME": os.environ.get("HOME", ""),
        "USERPROFILE": os.environ.get("USERPROFILE", ""),
        "HOMEDRIVE": os.environ.get("HOMEDRIVE", ""),
        "HOMEPATH": os.environ.get("HOMEPATH", ""),
        "Path.home()": str(Path.home()),
        "os.path.expanduser(\"~\")": os.path.expanduser("~"),
    }
    resolved_directories = {
        name: existing_directory(value)
        for name, value in values.items()
        if name not in {"HOMEDRIVE", "HOMEPATH"}
    }
    resolved_directories["HOMEDRIVE+HOMEPATH"] = existing_directory(
        os.path.join(values["HOMEDRIVE"], values["HOMEPATH"])
    )
    selected, expanduser_home = canonical_home()
    result = {
        "environment": values,
        "resolved_directories": resolved_directories,
        "canonical_home": selected,
        "canonical_home_exists": selected is not None,
        "expanduser_home": expanduser_home,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if selected is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
