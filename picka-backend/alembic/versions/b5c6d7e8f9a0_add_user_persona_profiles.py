"""add user persona profiles

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b5c6d7e8f9a0"
down_revision: str | None = "a4b5c6d7e8f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_persona_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("persona_id", sa.String(length=50), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=30), nullable=True),
        sa.Column("job", sa.String(length=200), nullable=True),
        sa.Column("residence", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("monthly_budget", sa.Integer(), nullable=True),
        sa.Column("period", sa.String(length=7), nullable=True),
        sa.Column("preferred_benefits", sa.Text(), nullable=True),
        sa.Column("source_payload", sa.JSON(), nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("persona_id"),
    )
    op.create_index(
        "ix_user_persona_profiles_user_id",
        "user_persona_profiles",
        ["user_id"],
    )
    op.create_index(
        "ix_user_persona_profiles_persona_id",
        "user_persona_profiles",
        ["persona_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_persona_profiles_persona_id",
        table_name="user_persona_profiles",
    )
    op.drop_index(
        "ix_user_persona_profiles_user_id",
        table_name="user_persona_profiles",
    )
    op.drop_table("user_persona_profiles")
