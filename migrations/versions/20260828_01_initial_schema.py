"""Create the initial shift and pause tables.

Revision ID: 20260828_01
Revises:
Create Date: 2026-08-28
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260828_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shift",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("automatically_closed", sa.Boolean(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(finished_at IS NULL) OR (started_at < finished_at)",
            name="check_started_before_finished",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pause",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shift_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(finished_at IS NULL) OR (started_at < finished_at)",
            name="check_started_before_finished",
        ),
        sa.ForeignKeyConstraint(["shift_id"], ["shift.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pause")
    op.drop_table("shift")
