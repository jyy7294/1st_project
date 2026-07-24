"""add structured persona contact, children, and region fields

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_persona_profiles", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("phone_number", sa.String(30), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("memberships", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("user_persona_profiles", sa.Column("is_foreigner", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("user_persona_profiles", sa.Column("residence_sido", sa.String(100), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("residence_sigungu", sa.String(100), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("child_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_persona_profiles", sa.Column("children_age_reference_date", sa.Date(), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("children", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    for column in (
        "children", "children_age_reference_date", "child_count",
        "residence_sigungu", "residence_sido", "is_foreigner",
        "memberships", "phone_number", "birth_date",
    ):
        op.drop_column("user_persona_profiles", column)
