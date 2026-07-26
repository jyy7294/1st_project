"""add user eligibilities

Revision ID: d1e2f3a4b5c6
Revises: c8d4e6f2a901
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "c8d4e6f2a901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_eligibilities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("eligibility_type", sa.String(length=100), nullable=False),
        sa.Column("eligibility_value", sa.String(length=255), nullable=False),
        sa.Column("verification_status", sa.String(length=30), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "user_id",
            "eligibility_type",
            name="uq_user_eligibilities_user_type",
        ),
    )
    op.create_index(
        "ix_user_eligibilities_user_id",
        "user_eligibilities",
        ["user_id"],
    )
    op.create_index(
        "ix_user_eligibilities_eligibility_type",
        "user_eligibilities",
        ["eligibility_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_eligibilities_eligibility_type",
        table_name="user_eligibilities",
    )
    op.drop_index(
        "ix_user_eligibilities_user_id",
        table_name="user_eligibilities",
    )
    op.drop_table("user_eligibilities")
