"""add transactions table

Revision ID: b96f7e2d4a31
Revises: 87ca6a1f1d04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b96f7e2d4a31"
down_revision: str | None = "87ca6a1f1d04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_card_id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("merchant_name", sa.String(length=255), nullable=False),
        sa.Column("payment_category", sa.String(length=100), nullable=True),
        sa.Column("original_payment_amount", sa.Integer(), nullable=False),
        sa.Column(
            "saved_amount",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("final_approved_amount", sa.Integer(), nullable=False),
        sa.Column("applied_benefit_name", sa.Text(), nullable=True),
        sa.Column(
            "applied_benefit_category",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "approval_number",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="APPROVED",
            nullable=False,
        ),
        sa.Column("usage_month", sa.String(length=7), nullable=False),
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "original_payment_amount > 0",
            name="ck_transactions_original_amount_positive",
        ),
        sa.CheckConstraint(
            "saved_amount >= 0",
            name="ck_transactions_saved_amount_nonnegative",
        ),
        sa.CheckConstraint(
            "final_approved_amount >= 0",
            name="ck_transactions_final_amount_nonnegative",
        ),
        sa.CheckConstraint(
            "saved_amount <= original_payment_amount",
            name="ck_transactions_saved_not_over_original",
        ),
        sa.CheckConstraint(
            "final_approved_amount = original_payment_amount - saved_amount",
            name="ck_transactions_amounts_consistent",
        ),
        sa.ForeignKeyConstraint(
            ["card_id"], ["cards.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_card_id"], ["user_cards.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "approval_number",
            name="uq_transactions_approval_number",
        ),
    )
    op.create_index(
        "ix_transactions_usage_month",
        "transactions",
        ["usage_month"],
    )
    op.create_index(
        "ix_transactions_user_approved_at",
        "transactions",
        ["user_id", "approved_at"],
    )
    op.create_index(
        "ix_transactions_user_card_approved_at",
        "transactions",
        ["user_id", "card_id", "approved_at"],
    )
    op.create_index(
        "ix_transactions_user_card_record_approved_at",
        "transactions",
        ["user_card_id", "approved_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transactions_user_card_record_approved_at",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_user_card_approved_at",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_user_approved_at",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_usage_month",
        table_name="transactions",
    )
    op.drop_table("transactions")
