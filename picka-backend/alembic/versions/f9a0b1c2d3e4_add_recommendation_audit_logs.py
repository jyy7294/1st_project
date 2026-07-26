"""add recommendation audit logs

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f9a0b1c2d3e4"
down_revision: str | None = "e8f9a0b1c2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recommendation_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_kind", sa.String(length=50), nullable=False),
        sa.Column("usage_month", sa.String(length=7), nullable=True),
        sa.Column("selected_card_id", sa.Integer(), sa.ForeignKey("cards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("calculation_payload", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=100), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("request_id", "user_id", "request_kind", "usage_month", "created_at"):
        op.create_index(f"ix_recommendation_audit_logs_{column}", "recommendation_audit_logs", [column])


def downgrade() -> None:
    for column in ("created_at", "usage_month", "request_kind", "user_id", "request_id"):
        op.drop_index(f"ix_recommendation_audit_logs_{column}", table_name="recommendation_audit_logs")
    op.drop_table("recommendation_audit_logs")
