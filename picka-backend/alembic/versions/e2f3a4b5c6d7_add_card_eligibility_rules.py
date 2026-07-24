"""add card eligibility rules

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "card_eligibility_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "card_id",
            sa.Integer(),
            sa.ForeignKey("cards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("eligibility_type", sa.String(length=100), nullable=False),
        sa.Column(
            "comparison_operator",
            sa.String(length=10),
            server_default="EQ",
            nullable=False,
        ),
        sa.Column("required_value", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "card_id",
            "eligibility_type",
            name="uq_card_eligibility_rules_card_type",
        ),
    )
    op.create_index(
        "ix_card_eligibility_rules_card_id",
        "card_eligibility_rules",
        ["card_id"],
    )
    op.create_index(
        "ix_card_eligibility_rules_eligibility_type",
        "card_eligibility_rules",
        ["eligibility_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_card_eligibility_rules_eligibility_type",
        table_name="card_eligibility_rules",
    )
    op.drop_index(
        "ix_card_eligibility_rules_card_id",
        table_name="card_eligibility_rules",
    )
    op.drop_table("card_eligibility_rules")
