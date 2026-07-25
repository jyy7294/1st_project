"""remove remaining plaintext identity fields and social provider

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a2b3c4d5e6f7"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for column in ("email_encrypted", "email_blind_index", "name_encrypted"):
        existing = sa.String(64) if column == "email_blind_index" else sa.Text()
        op.alter_column("users", column, existing_type=existing, nullable=False)
    op.drop_column("users", "provider")
    op.drop_column("users", "email")
    op.drop_column("users", "name")

    for column in ("age_encrypted", "is_foreigner_encrypted", "child_count_encrypted"):
        op.alter_column(
            "user_persona_profiles",
            column,
            existing_type=sa.Text(),
            nullable=False,
        )
    for column in ("age", "gender", "job", "is_foreigner", "child_count"):
        op.drop_column("user_persona_profiles", column)


def downgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(320), nullable=True))
    op.add_column("users", sa.Column("name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("provider", sa.String(30), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("gender", sa.String(30), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("job", sa.String(200), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("is_foreigner", sa.Boolean(), nullable=True))
    op.add_column("user_persona_profiles", sa.Column("child_count", sa.Integer(), nullable=True))
