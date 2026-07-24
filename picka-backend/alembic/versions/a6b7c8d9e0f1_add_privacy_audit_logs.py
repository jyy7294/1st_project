"""add privacy change audit logs

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a6b7c8d9e0f1"
down_revision: str | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "privacy_audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_privacy_audit_logs_actor_user_id", "privacy_audit_logs", ["actor_user_id"])
    op.create_index("ix_privacy_audit_logs_target_user_id", "privacy_audit_logs", ["target_user_id"])
    op.create_index("ix_privacy_audit_logs_action", "privacy_audit_logs", ["action"])
    op.create_index("ix_privacy_audit_logs_created_at", "privacy_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_privacy_audit_logs_created_at", table_name="privacy_audit_logs")
    op.drop_index("ix_privacy_audit_logs_action", table_name="privacy_audit_logs")
    op.drop_index("ix_privacy_audit_logs_target_user_id", table_name="privacy_audit_logs")
    op.drop_index("ix_privacy_audit_logs_actor_user_id", table_name="privacy_audit_logs")
    op.drop_table("privacy_audit_logs")
