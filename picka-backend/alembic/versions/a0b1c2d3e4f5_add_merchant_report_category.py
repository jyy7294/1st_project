"""add merchant report category

Revision ID: a0b1c2d3e4f5
Revises: f9a0b1c2d3e4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "f9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "merchant_aliases",
        sa.Column("report_category", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("merchant_aliases", "report_category")
