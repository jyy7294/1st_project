"""add card benefit eligibility rules

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f3a4b5c6d7e8"
down_revision: str | None = "e2f3a4b5c6d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "card_benefit_eligibility_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "card_benefit_id",
            sa.Integer(),
            sa.ForeignKey("card_benefits.id", ondelete="CASCADE"),
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
            "card_benefit_id",
            "eligibility_type",
            "required_value",
            name="uq_card_benefit_eligibility_rules_benefit_type_value",
        ),
    )
    op.create_index(
        "ix_card_benefit_eligibility_rules_benefit_id",
        "card_benefit_eligibility_rules",
        ["card_benefit_id"],
    )
    op.create_index(
        "ix_card_benefit_eligibility_rules_eligibility_type",
        "card_benefit_eligibility_rules",
        ["eligibility_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_card_benefit_eligibility_rules_eligibility_type",
        table_name="card_benefit_eligibility_rules",
    )
    op.drop_index(
        "ix_card_benefit_eligibility_rules_benefit_id",
        table_name="card_benefit_eligibility_rules",
    )
    op.drop_table("card_benefit_eligibility_rules")
