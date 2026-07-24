"""add encrypted shadow columns for staged PII migration

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "a6b7c8d9e0f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for column in (
        "birth_date_encrypted",
        "phone_number_encrypted",
        "residence_encrypted",
        "memberships_encrypted",
        "children_encrypted",
    ):
        op.add_column(
            "user_persona_profiles",
            sa.Column(column, sa.Text(), nullable=True),
        )
    op.add_column(
        "user_eligibilities",
        sa.Column("eligibility_value_encrypted", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_eligibilities", "eligibility_value_encrypted")
    for column in (
        "children_encrypted",
        "memberships_encrypted",
        "residence_encrypted",
        "phone_number_encrypted",
        "birth_date_encrypted",
    ):
        op.drop_column("user_persona_profiles", column)
