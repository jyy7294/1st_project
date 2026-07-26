"""add authentication fields and social accounts

Revision ID: d4a32bc890fe
Revises: b96f7e2d4a31
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d4a32bc890fe"
down_revision: str | None = "b96f7e2d4a31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column(
            "provider_user_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column(
            "profile_image_url",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_social_accounts_provider_user",
        ),
    )
    op.create_index(
        "ix_social_accounts_user_id",
        "social_accounts",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_social_accounts_user_id",
        table_name="social_accounts",
    )
    op.drop_table("social_accounts")
    op.drop_column("users", "is_active")
    op.drop_column("users", "password_hash")
