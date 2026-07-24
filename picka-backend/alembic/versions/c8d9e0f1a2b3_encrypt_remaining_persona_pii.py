"""add encrypted columns for remaining persona PII

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c8d9e0f1a2b3"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for column in (
        "residence_sido_encrypted",
        "residence_sigungu_encrypted",
        "children_age_reference_date_encrypted",
        "source_payload_encrypted",
    ):
        op.add_column(
            "user_persona_profiles",
            sa.Column(column, sa.Text(), nullable=True),
        )


def downgrade() -> None:
    for column in (
        "source_payload_encrypted",
        "children_age_reference_date_encrypted",
        "residence_sigungu_encrypted",
        "residence_sido_encrypted",
    ):
        op.drop_column("user_persona_profiles", column)
