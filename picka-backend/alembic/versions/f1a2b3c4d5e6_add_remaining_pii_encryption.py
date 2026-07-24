"""add encrypted identity fields and email blind index

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e0f1a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("email_blind_index", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("name_encrypted", sa.Text(), nullable=True))
    op.create_index("ix_users_email_blind_index", "users", ["email_blind_index"], unique=True)
    for column in (
        "age_encrypted",
        "gender_encrypted",
        "job_encrypted",
        "is_foreigner_encrypted",
        "child_count_encrypted",
    ):
        op.add_column("user_persona_profiles", sa.Column(column, sa.Text(), nullable=True))


def downgrade() -> None:
    for column in (
        "child_count_encrypted",
        "is_foreigner_encrypted",
        "job_encrypted",
        "gender_encrypted",
        "age_encrypted",
    ):
        op.drop_column("user_persona_profiles", column)
    op.drop_index("ix_users_email_blind_index", table_name="users")
    op.drop_column("users", "name_encrypted")
    op.drop_column("users", "email_blind_index")
    op.drop_column("users", "email_encrypted")
