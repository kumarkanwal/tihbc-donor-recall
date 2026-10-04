"""Tests for isolated PostgreSQL test-database URL selection."""

import pytest

from tests.postgres_setup import resolve_test_database_url


def test_test_database_defaults_to_separate_database_on_same_server() -> None:
    resolved = resolve_test_database_url(
        "postgresql+asyncpg://user:secret@localhost:5433/tihbc",
        None,
    )

    assert resolved == "postgresql+asyncpg://user:secret@localhost:5433/tihbc_test"


def test_explicit_test_database_url_is_preserved() -> None:
    resolved = resolve_test_database_url(
        "postgresql+asyncpg://user:secret@localhost:5433/tihbc",
        "postgresql+asyncpg://tester:other@db.example:5432/isolated_tests",
    )

    assert resolved == "postgresql+asyncpg://tester:other@db.example:5432/isolated_tests"


def test_development_database_is_rejected_as_test_database() -> None:
    database_url = "postgresql+asyncpg://user:secret@localhost:5433/tihbc"

    with pytest.raises(ValueError, match="different database"):
        resolve_test_database_url(database_url, database_url)
