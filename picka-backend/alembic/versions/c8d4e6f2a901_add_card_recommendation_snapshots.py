"""add card recommendation snapshots

Revision ID: c8d4e6f2a901
Revises: a7b9c2d4e601
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "c8d4e6f2a901"
down_revision: str | None = "a7b9c2d4e601"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "card_recommendation_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("credit_result", sa.JSON(), nullable=False),
        sa.Column("check_result", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "analysis_date", name="uq_card_recommendation_snapshot_user_date"),
    )
    op.create_index("ix_card_recommendation_snapshots_user_id", "card_recommendation_snapshots", ["user_id"])
    op.create_index("ix_card_recommendation_snapshots_analysis_date", "card_recommendation_snapshots", ["analysis_date"])

def downgrade() -> None:
    op.drop_index("ix_card_recommendation_snapshots_analysis_date", table_name="card_recommendation_snapshots")
    op.drop_index("ix_card_recommendation_snapshots_user_id", table_name="card_recommendation_snapshots")
    op.drop_table("card_recommendation_snapshots")
