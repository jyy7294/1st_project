"""add transaction rewards

Revision ID: a7b9c2d4e601
Revises: f3c12a7d9e01
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "a7b9c2d4e601"
down_revision: str | None = "f3c12a7d9e01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "transaction_rewards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_benefit_id", sa.Integer(), sa.ForeignKey("card_benefits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reward_type", sa.String(20), nullable=False),
        sa.Column("reward_program", sa.String(100), nullable=False),
        sa.Column("reward_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("reward_unit", sa.String(20), nullable=False),
    )
    op.create_index("ix_transaction_rewards_transaction_id", "transaction_rewards", ["transaction_id"])

def downgrade() -> None:
    op.drop_index("ix_transaction_rewards_transaction_id", table_name="transaction_rewards")
    op.drop_table("transaction_rewards")
