from pathlib import Path

import pytest

from codex_flow.api.config import ServiceConfig
from codex_flow.codex_adapter.fake import FakeCodexAdapter
from codex_flow.runtime.manager import RuntimeManager
from codex_flow.storage.db import open_database
from codex_flow.storage.repositories import StorageRepositories


def test_service_config_defaults_to_one_global_slot() -> None:
    assert ServiceConfig.default().max_concurrency == 1
    assert ServiceConfig.from_db_path(Path("flow.sqlite3")).max_concurrency == 1


@pytest.mark.parametrize("value", [0, -1])
def test_service_config_rejects_non_positive_global_capacity(value: int) -> None:
    with pytest.raises(ValueError, match="max_concurrency must be positive"):
        ServiceConfig.from_db_path(Path("flow.sqlite3"), max_concurrency=value)


def test_runtime_manager_receives_configured_global_capacity(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))
    manager = RuntimeManager(repository, FakeCodexAdapter(), max_concurrency=3)

    assert manager.max_concurrency == 3


def test_runtime_manager_rejects_non_positive_global_capacity(tmp_path: Path) -> None:
    repository = StorageRepositories(open_database(tmp_path / "flow.sqlite3"))

    with pytest.raises(ValueError, match="max_concurrency must be positive"):
        RuntimeManager(repository, FakeCodexAdapter(), max_concurrency=0)
