"""add recommendation policy version

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a4b5c6d7e8f9"
down_revision: str | None = "f3a4b5c6d7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "card_recommendation_snapshots",
        sa.Column(
            "policy_version",
            sa.String(length=100),
            nullable=False,
            server_default="legacy",
        ),
    )
    op.alter_column(
        "card_recommendation_snapshots",
        "policy_version",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("card_recommendation_snapshots", "policy_version")
