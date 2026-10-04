"""Insert required segment and demo-clock reference rows.

Revision ID: 0002_reference_data
Revises: 0001_initial_schema
Create Date: 2026-10-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_reference_data"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEGMENTS = (
    {
        "id": "00000000-0000-4000-8000-000000000001",
        "key": "regular",
        "label": "Regular",
    },
    {
        "id": "00000000-0000-4000-8000-000000000002",
        "key": "lapsed",
        "label": "Lapsed",
    },
    {
        "id": "00000000-0000-4000-8000-000000000003",
        "key": "first_time",
        "label": "First-time",
    },
)


def upgrade() -> None:
    """Insert reference rows required by application startup and imports."""
    segments = sa.table(
        "segments",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String()),
        sa.column("label", sa.String()),
    )
    demo_clock = sa.table(
        "demo_clock",
        sa.column("id", sa.SmallInteger()),
        sa.column("offset_seconds", sa.BigInteger()),
    )
    op.bulk_insert(segments, list(SEGMENTS))
    op.bulk_insert(demo_clock, [{"id": 1, "offset_seconds": 0}])


def downgrade() -> None:
    """Remove only the reference rows owned by this migration."""
    op.execute(sa.text("DELETE FROM demo_clock WHERE id = 1"))
    op.execute(sa.text("DELETE FROM segments WHERE key IN ('regular', 'lapsed', 'first_time')"))
