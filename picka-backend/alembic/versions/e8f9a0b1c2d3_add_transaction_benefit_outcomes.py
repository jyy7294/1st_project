"""add transaction benefit outcomes

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e8f9a0b1c2d3"
down_revision: str | None = "d7e8f9a0b1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "user_persona_profiles",
        "period",
        existing_type=sa.String(length=7),
        type_=sa.String(length=30),
        existing_nullable=True,
    )
    op.create_table(
        "transaction_benefit_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "recommended_card_id",
            sa.Integer(),
            sa.ForeignKey("cards.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "card_benefit_id",
            sa.Integer(),
            sa.ForeignKey("card_benefits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("benefit_scenario", sa.String(length=50), nullable=False),
        sa.Column("picka_usage_stage", sa.String(length=50), nullable=False),
        sa.Column("actual_benefit_amount", sa.Integer(), nullable=False),
        sa.Column("potential_benefit_amount", sa.Integer(), nullable=False),
        sa.Column("missed_benefit_amount", sa.Integer(), nullable=False),
        sa.Column("missed_benefit_reason", sa.Text(), nullable=True),
        sa.Column("benefit_rate_text", sa.String(length=50), nullable=True),
        sa.Column("monthly_benefit_cap", sa.Integer(), nullable=True),
        sa.Column("cap_remaining_before", sa.Integer(), nullable=True),
        sa.Column("cap_remaining_after", sa.Integer(), nullable=True),
        sa.Column("judgement_source", sa.String(length=100), nullable=True),
        sa.Column("reward_type", sa.String(length=30), nullable=True),
        sa.Column("reward_program", sa.Text(), nullable=True),
        sa.Column("reward_amount", sa.Integer(), nullable=True),
        sa.Column("reward_unit", sa.String(length=20), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_transaction_benefit_outcomes_transaction_id",
        "transaction_benefit_outcomes",
        ["transaction_id"],
        unique=True,
    )
    op.create_index(
        "ix_transaction_benefit_outcomes_recommended_card_id",
        "transaction_benefit_outcomes",
        ["recommended_card_id"],
    )
    op.create_index(
        "ix_transaction_benefit_outcomes_card_benefit_id",
        "transaction_benefit_outcomes",
        ["card_benefit_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transaction_benefit_outcomes_card_benefit_id",
        table_name="transaction_benefit_outcomes",
    )
    op.drop_index(
        "ix_transaction_benefit_outcomes_recommended_card_id",
        table_name="transaction_benefit_outcomes",
    )
    op.drop_index(
        "ix_transaction_benefit_outcomes_transaction_id",
        table_name="transaction_benefit_outcomes",
    )
    op.drop_table("transaction_benefit_outcomes")
    op.alter_column(
        "user_persona_profiles",
        "period",
        existing_type=sa.String(length=30),
        type_=sa.String(length=7),
        existing_nullable=True,
    )
