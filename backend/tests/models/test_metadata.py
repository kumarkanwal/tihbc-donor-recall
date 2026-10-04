"""Tests for schema metadata shared by models and Alembic."""

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import configure_mappers

from app.models import Base

EXPECTED_TABLES = {
    "appointment_slots",
    "campaigns",
    "content_series",
    "demo_clock",
    "donor_batches",
    "donor_responses",
    "donors",
    "enrollments",
    "follow_up_activities",
    "follow_up_items",
    "messages",
    "segments",
    "series_step_contents",
    "series_steps",
    "series_tags",
    "tags",
    "users",
}


def test_all_expected_tables_and_mappers_are_registered() -> None:
    configure_mappers()
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_entity_tables_have_primary_keys_and_timestamps() -> None:
    for table_name, table in Base.metadata.tables.items():
        if table_name == "series_tags":
            assert tuple(column.name for column in table.primary_key.columns) == (
                "series_id",
                "tag_id",
            )
            continue

        assert {"id", "created_at", "updated_at"}.issubset(table.columns.keys())
        assert table.c.id.primary_key
        if table_name == "demo_clock":
            assert not isinstance(table.c.id.type, PostgreSQLUUID)
        else:
            assert isinstance(table.c.id.type, PostgreSQLUUID)


def test_every_foreign_key_column_has_a_leading_index() -> None:
    for table in Base.metadata.tables.values():
        leading_index_columns = {
            tuple(index.columns)[0].name for index in table.indexes if tuple(index.columns)
        }
        for foreign_key in table.foreign_keys:
            assert foreign_key.parent.name in leading_index_columns


def test_only_specified_foreign_keys_cascade_on_delete() -> None:
    cascading_foreign_keys = {
        (foreign_key.parent.table.name, foreign_key.parent.name)
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
        if foreign_key.ondelete == "CASCADE"
    }
    assert cascading_foreign_keys == {
        ("donors", "batch_id"),
        ("series_steps", "series_id"),
        ("series_step_contents", "step_id"),
    }


def test_required_unique_constraints_are_present() -> None:
    expected = {
        ("users", ("email",)),
        ("segments", ("key",)),
        ("tags", ("name",)),
        ("donors", ("batch_id", "phone_e164")),
        ("series_steps", ("series_id", "step_order")),
        ("series_step_contents", ("step_id", "language")),
        ("enrollments", ("campaign_id", "donor_id")),
    }
    actual = {
        (table.name, tuple(column.name for column in constraint.columns))
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert expected.issubset(actual)


def test_follow_up_open_item_index_is_partial_and_unique() -> None:
    index = next(
        index
        for index in Base.metadata.tables["follow_up_items"].indexes
        if index.name == "uq_follow_up_items_open_enrollment"
    )
    assert isinstance(index, Index)
    assert index.unique is True
    assert str(index.dialect_options["postgresql"]["where"]) == (
        "status <> 'done'::follow_up_status"
    )


def test_database_invariants_have_check_constraints() -> None:
    checks = {
        (table.name, constraint.name)
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert checks == {
        ("appointment_slots", "ck_appointment_slots_booked_count_within_capacity"),
        ("demo_clock", "ck_demo_clock_singleton_id"),
        ("series_step_contents", "ck_series_step_contents_body_max_length"),
        ("series_steps", "ck_series_steps_step_order_positive"),
    }
