"""add source benefit id

Revision ID: b731d3d716a1
Revises: a25835462073
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b731d3d716a1"
down_revision: Union[str, Sequence[str], None] = "a25835462073"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "card_benefits",
        sa.Column(
            "source_benefit_id",
            sa.String(length=50),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_card_benefits_source_benefit_id"),
        "card_benefits",
        ["source_benefit_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_card_benefits_source_benefit_id"),
        table_name="card_benefits",
    )
    op.drop_column("card_benefits", "source_benefit_id")
