"""Tests for per-process container migration ownership."""

from pathlib import Path

import pytest
from alembic.config import Config

from app.core.config import Settings
from app.core.run_migrations import run_configured_migrations


def test_api_process_runs_migrations() -> None:
    calls: list[tuple[str | None, str]] = []

    def upgrade(config: Config, revision: str) -> None:
        calls.append((config.config_file_name, revision))

    settings = Settings(run_migrations=True)

    applied = run_configured_migrations(
        settings,
        config_path=Path("test-alembic.ini"),
        migration_runner=upgrade,
    )

    assert applied is True
    assert calls == [("test-alembic.ini", "head")]


def test_worker_process_skips_migrations() -> None:
    def unexpected_upgrade(config: Config, revision: str) -> None:
        del config, revision
        pytest.fail("worker attempted to run migrations")

    settings = Settings(run_migrations=False)

    assert run_configured_migrations(settings, migration_runner=unexpected_upgrade) is False
