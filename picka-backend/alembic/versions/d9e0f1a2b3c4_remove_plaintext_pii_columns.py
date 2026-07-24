"""remove plaintext PII after encrypted-read verification

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d9e0f1a2b3c4"
down_revision: str | None = "c8d9e0f1a2b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "user_eligibilities",
        "eligibility_value_encrypted",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.drop_column("user_eligibilities", "eligibility_value")

    for column in (
        "memberships_encrypted",
        "children_encrypted",
        "source_payload_encrypted",
    ):
        op.alter_column(
            "user_persona_profiles",
            column,
            existing_type=sa.Text(),
            nullable=False,
        )
    for column in (
        "birth_date",
        "phone_number",
        "memberships",
        "residence",
        "residence_sido",
        "residence_sigungu",
        "children_age_reference_date",
        "children",
        "source_payload",
    ):
        op.drop_column("user_persona_profiles", column)


def downgrade() -> None:
    # Downgrade recreates empty compatibility columns only; encrypted PII is not
    # decrypted inside a schema migration.
    op.add_column(
        "user_eligibilities",
        sa.Column("eligibility_value", sa.String(length=255), nullable=True),
    )
    op.alter_column(
        "user_eligibilities",
        "eligibility_value_encrypted",
        existing_type=sa.Text(),
        nullable=True,
    )
    columns = (
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("memberships", sa.JSON(), nullable=True),
        sa.Column("residence", sa.String(length=200), nullable=True),
        sa.Column("residence_sido", sa.String(length=100), nullable=True),
        sa.Column("residence_sigungu", sa.String(length=100), nullable=True),
        sa.Column("children_age_reference_date", sa.Date(), nullable=True),
        sa.Column("children", sa.JSON(), nullable=True),
        sa.Column("source_payload", sa.JSON(), nullable=True),
    )
    for column in columns:
        op.add_column("user_persona_profiles", column)
    for column in (
        "memberships_encrypted",
        "children_encrypted",
        "source_payload_encrypted",
    ):
        op.alter_column(
            "user_persona_profiles",
            column,
            existing_type=sa.Text(),
            nullable=True,
        )
