"""create card benefit merchant tables

Revision ID: a25835462073
Revises: 
Create Date: 2026-07-20 00:17:18.564213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a25835462073'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_card_id", sa.Integer(), nullable=True),
        sa.Column("card_name", sa.String(length=200), nullable=False),
        sa.Column("issuer", sa.String(length=100), nullable=True),
        sa.Column("card_type", sa.String(length=50), nullable=True),
        sa.Column("annual_fee", sa.Integer(), nullable=True),
        sa.Column("previous_spending", sa.Integer(), nullable=True),
        sa.Column("monthly_total_limit", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cards_card_name"), "cards", ["card_name"])
    op.create_index(op.f("ix_cards_issuer"), "cards", ["issuer"])
    op.create_index(
        op.f("ix_cards_source_card_id"),
        "cards",
        ["source_card_id"],
        unique=True,
    )

    op.create_table(
        "merchant_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alias", sa.String(length=300), nullable=False),
        sa.Column("normalized_name", sa.String(length=200), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alias",
            "category",
            name="uq_merchant_alias_category",
        ),
    )
    op.create_index(
        op.f("ix_merchant_aliases_alias"),
        "merchant_aliases",
        ["alias"],
    )
    op.create_index(
        op.f("ix_merchant_aliases_category"),
        "merchant_aliases",
        ["category"],
    )
    op.create_index(
        op.f("ix_merchant_aliases_normalized_name"),
        "merchant_aliases",
        ["normalized_name"],
    )

    op.create_table(
        "card_benefits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("benefit_name", sa.String(length=500), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("benefit_type", sa.String(length=100), nullable=True),
        sa.Column("benefit_unit", sa.String(length=50), nullable=True),
        sa.Column("benefit_value", sa.Float(), nullable=True),
        sa.Column("required_spending", sa.Integer(), nullable=True),
        sa.Column("minimum_payment", sa.Integer(), nullable=True),
        sa.Column("per_transaction_limit", sa.Integer(), nullable=True),
        sa.Column("monthly_spending_limit", sa.Integer(), nullable=True),
        sa.Column("monthly_benefit_limit", sa.Integer(), nullable=True),
        sa.Column("daily_count_limit", sa.Integer(), nullable=True),
        sa.Column("monthly_count_limit", sa.Integer(), nullable=True),
        sa.Column("annual_limit", sa.Integer(), nullable=True),
        sa.Column("limit_status", sa.String(length=100), nullable=True),
        sa.Column("condition_text", sa.Text(), nullable=True),
        sa.Column("exception_text", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("additional_conditions", sa.JSON(), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["cards.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_card_benefits_card_id"),
        "card_benefits",
        ["card_id"],
    )
    op.create_index(
        op.f("ix_card_benefits_category"),
        "card_benefits",
        ["category"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_card_benefits_category"),
        table_name="card_benefits",
    )
    op.drop_index(
        op.f("ix_card_benefits_card_id"),
        table_name="card_benefits",
    )
    op.drop_table("card_benefits")

    op.drop_index(
        op.f("ix_merchant_aliases_normalized_name"),
        table_name="merchant_aliases",
    )
    op.drop_index(
        op.f("ix_merchant_aliases_category"),
        table_name="merchant_aliases",
    )
    op.drop_index(
        op.f("ix_merchant_aliases_alias"),
        table_name="merchant_aliases",
    )
    op.drop_table("merchant_aliases")

    op.drop_index(op.f("ix_cards_source_card_id"), table_name="cards")
    op.drop_index(op.f("ix_cards_issuer"), table_name="cards")
    op.drop_index(op.f("ix_cards_card_name"), table_name="cards")
    op.drop_table("cards")
