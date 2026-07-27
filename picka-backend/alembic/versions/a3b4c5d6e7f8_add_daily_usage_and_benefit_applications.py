"""add daily benefit usage and transaction benefit applications

Revision ID: a3b4c5d6e7f8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a3b4c5d6e7f8"
down_revision: str | None = "a2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "benefit_daily_usage",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.Integer(), sa.ForeignKey("cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_benefit_id", sa.Integer(), sa.ForeignKey("card_benefits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("daily_used_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("daily_used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("daily_used_amount >= 0", name="ck_benefit_daily_usage_amount_nonnegative"),
        sa.CheckConstraint("daily_used_count >= 0", name="ck_benefit_daily_usage_count_nonnegative"),
        sa.UniqueConstraint("user_id", "card_benefit_id", "usage_date", name="uq_benefit_daily_usage_user_benefit_date"),
    )
    op.create_index("ix_benefit_daily_usage_user_id", "benefit_daily_usage", ["user_id"])
    op.create_index("ix_benefit_daily_usage_card_id", "benefit_daily_usage", ["card_id"])
    op.create_index("ix_benefit_daily_usage_card_benefit_id", "benefit_daily_usage", ["card_benefit_id"])
    op.create_index("ix_benefit_daily_usage_usage_date", "benefit_daily_usage", ["usage_date"])

    op.create_table(
        "transaction_benefit_applications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_benefit_id", sa.Integer(), sa.ForeignKey("card_benefits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("applied_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applied_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="APPLIED"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("applied_amount >= 0", name="ck_transaction_benefit_applications_amount_nonnegative"),
        sa.CheckConstraint("applied_count > 0", name="ck_transaction_benefit_applications_count_positive"),
        sa.CheckConstraint("status IN ('APPLIED', 'REVERSED')", name="ck_transaction_benefit_applications_status"),
        sa.UniqueConstraint("transaction_id", "card_benefit_id", name="uq_transaction_benefit_application_transaction_benefit"),
    )
    op.create_index("ix_transaction_benefit_applications_transaction_id", "transaction_benefit_applications", ["transaction_id"])
    op.create_index("ix_transaction_benefit_applications_card_benefit_id", "transaction_benefit_applications", ["card_benefit_id"])

    # Only backfill rows whose benefit FK is already unambiguous.
    op.execute("""
        INSERT INTO transaction_benefit_applications (
            transaction_id, card_benefit_id, applied_amount, applied_count,
            status, applied_at, created_at, updated_at
        )
        SELECT t.id, o.card_benefit_id, t.saved_amount, 1,
               'APPLIED', t.approved_at, NOW(), NOW()
        FROM transactions AS t
        JOIN transaction_benefit_outcomes AS o ON o.transaction_id = t.id
        WHERE t.status = 'APPROVED'
          AND t.saved_amount > 0
          AND o.card_benefit_id IS NOT NULL
        ON CONFLICT (transaction_id, card_benefit_id) DO NOTHING
    """)
    op.execute("""
        INSERT INTO benefit_daily_usage (
            user_id, card_id, card_benefit_id, usage_date,
            daily_used_amount, daily_used_count, created_at, updated_at
        )
        SELECT t.user_id, t.card_id, a.card_benefit_id,
               (t.approved_at AT TIME ZONE 'Asia/Seoul')::date,
               SUM(a.applied_amount)::integer,
               SUM(a.applied_count)::integer,
               NOW(), NOW()
        FROM transaction_benefit_applications AS a
        JOIN transactions AS t ON t.id = a.transaction_id
        WHERE a.status = 'APPLIED'
        GROUP BY t.user_id, t.card_id, a.card_benefit_id,
                 (t.approved_at AT TIME ZONE 'Asia/Seoul')::date
        ON CONFLICT (user_id, card_benefit_id, usage_date) DO NOTHING
    """)
    op.drop_column("benefit_usage", "daily_used_count")


def downgrade() -> None:
    op.add_column("benefit_usage", sa.Column("daily_used_count", sa.Integer(), nullable=False, server_default="0"))
    op.drop_index("ix_transaction_benefit_applications_card_benefit_id", table_name="transaction_benefit_applications")
    op.drop_index("ix_transaction_benefit_applications_transaction_id", table_name="transaction_benefit_applications")
    op.drop_table("transaction_benefit_applications")
    op.drop_index("ix_benefit_daily_usage_usage_date", table_name="benefit_daily_usage")
    op.drop_index("ix_benefit_daily_usage_card_benefit_id", table_name="benefit_daily_usage")
    op.drop_index("ix_benefit_daily_usage_card_id", table_name="benefit_daily_usage")
    op.drop_index("ix_benefit_daily_usage_user_id", table_name="benefit_daily_usage")
    op.drop_table("benefit_daily_usage")
