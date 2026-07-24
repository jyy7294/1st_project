"""remove all social login artifacts

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a0b1c2d3e4f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("social_accounts")
    op.drop_column("users", "provider")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("provider", sa.String(length=50), nullable=True),
    )
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("profile_image_url", sa.String(length=1000), nullable=True),
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
            ["user_id"], ["users.id"], ondelete="CASCADE"
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
