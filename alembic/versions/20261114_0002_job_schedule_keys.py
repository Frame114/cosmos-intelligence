"""Add unique schedule keys for deterministic job enqueueing."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261114_0002"
down_revision: str | None = "20261114_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ingestion_job", sa.Column("schedule_key", sa.String(length=255), nullable=True))
    op.create_index(
        "uq_ingestion_job_schedule_key",
        "ingestion_job",
        ["schedule_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_ingestion_job_schedule_key", table_name="ingestion_job")
    op.drop_column("ingestion_job", "schedule_key")
