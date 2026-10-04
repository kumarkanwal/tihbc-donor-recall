"""Tests for the Alembic revision chain and offline SQL compilation."""

from io import StringIO
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from alembic import command

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG = BACKEND_ROOT / "alembic.ini"


def _config() -> Config:
    config = Config(ALEMBIC_CONFIG)
    config.output_buffer = StringIO()
    return config


def test_reference_data_migration_is_the_only_head() -> None:
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == ["0002_reference_data"]
    reference_revision = scripts.get_revision("0002_reference_data")
    initial_revision = scripts.get_revision("0001_initial_schema")
    assert reference_revision is not None
    assert reference_revision.down_revision == "0001_initial_schema"
    assert initial_revision is not None
    assert initial_revision.down_revision is None


def test_initial_migration_compiles_to_postgresql_sql() -> None:
    config = _config()
    command.upgrade(config, "head", sql=True)
    output = config.output_buffer
    assert isinstance(output, StringIO)
    sql = output.getvalue()

    assert "CREATE TYPE user_role AS ENUM" in sql
    assert "CREATE TABLE users" in sql
    assert "CREATE TABLE follow_up_activities" in sql
    assert "CREATE UNIQUE INDEX uq_follow_up_items_open_enrollment" in sql
    assert "created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL" in sql
    assert "INSERT INTO segments" in sql
    assert "INSERT INTO demo_clock" in sql
    assert "INSERT INTO alembic_version" in sql
