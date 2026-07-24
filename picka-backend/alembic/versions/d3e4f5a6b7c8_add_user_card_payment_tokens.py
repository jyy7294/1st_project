"""add internal PG payment tokens to user cards

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_cards",
        sa.Column("payment_token", sa.String(length=80), nullable=True),
    )
    op.execute(
        "UPDATE user_cards "
        "SET payment_token = 'picka_pg_' || replace(gen_random_uuid()::text, '-', '') "
        "WHERE payment_token IS NULL"
    )
    op.alter_column("user_cards", "payment_token", nullable=False)
    op.create_index(
        "ix_user_cards_payment_token",
        "user_cards",
        ["payment_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_user_cards_payment_token", table_name="user_cards")
    op.drop_column("user_cards", "payment_token")
