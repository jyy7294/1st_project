"""add source detail to card benefits

Revision ID: 7c42b14f6e90
Revises: 1ed0a9a4b747
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c42b14f6e90"
down_revision: Union[str, Sequence[str], None] = "1ed0a9a4b747"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "card_benefits",
        sa.Column("source_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "card_benefits",
        sa.Column("source_detail", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("card_benefits", "source_detail")
    op.drop_column("card_benefits", "source_summary")
