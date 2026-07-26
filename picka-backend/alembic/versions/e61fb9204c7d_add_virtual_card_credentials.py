"""add virtual card credentials

Revision ID: e61fb9204c7d
Revises: d4a32bc890fe
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e61fb9204c7d"
down_revision: str | None = "d4a32bc890fe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "virtual_card_credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("card_number", sa.String(length=19), nullable=False),
        sa.Column("expiry_month", sa.Integer(), nullable=False),
        sa.Column("expiry_year", sa.Integer(), nullable=False),
        sa.Column("cvc", sa.String(length=3), nullable=False),
        sa.Column(
            "card_password_first2",
            sa.String(length=2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["card_id"], ["cards.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "card_number",
            name="uq_virtual_card_credentials_card_number",
        ),
    )
    op.create_index(
        "ix_virtual_card_credentials_card_id",
        "virtual_card_credentials",
        ["card_id"],
    )
    op.create_index(
        "ix_virtual_card_credentials_card_number",
        "virtual_card_credentials",
        ["card_number"],
        unique=True,
    )
    op.add_column(
        "user_cards",
        sa.Column("virtual_credential_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user_cards",
        sa.Column("card_number_last4", sa.String(length=4), nullable=True),
    )
    op.add_column(
        "user_cards",
        sa.Column("registration_method", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "user_cards",
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_user_cards_virtual_credential_id",
        "user_cards",
        ["virtual_credential_id"],
    )
    op.create_foreign_key(
        "fk_user_cards_virtual_credential_id",
        "user_cards",
        "virtual_card_credentials",
        ["virtual_credential_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_user_cards_virtual_credential_id",
        "user_cards",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_user_cards_virtual_credential_id",
        table_name="user_cards",
    )
    op.drop_column("user_cards", "registered_at")
    op.drop_column("user_cards", "registration_method")
    op.drop_column("user_cards", "card_number_last4")
    op.drop_column("user_cards", "virtual_credential_id")
    op.drop_index(
        "ix_virtual_card_credentials_card_number",
        table_name="virtual_card_credentials",
    )
    op.drop_index(
        "ix_virtual_card_credentials_card_id",
        table_name="virtual_card_credentials",
    )
    op.drop_table("virtual_card_credentials")
