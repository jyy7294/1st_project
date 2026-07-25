"""replace plaintext virtual credentials with mock vault boundary

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e0f1a2b3c4d5"
down_revision: str | None = "d9e0f1a2b3c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_user_cards_virtual_credential_id",
        "user_cards",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_user_cards_virtual_credential_id",
        table_name="user_cards",
    )
    op.drop_column("user_cards", "virtual_credential_id")
    op.drop_table("virtual_card_credentials")


def downgrade() -> None:
    op.create_table(
        "virtual_card_credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("card_number", sa.String(length=19), nullable=False),
        sa.Column("expiry_month", sa.Integer(), nullable=False),
        sa.Column("expiry_year", sa.Integer(), nullable=False),
        sa.Column("cvc", sa.String(length=3), nullable=False),
        sa.Column("card_password_first2", sa.String(length=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("card_number", name="uq_virtual_card_credentials_card_number"),
    )
    op.create_index("ix_virtual_card_credentials_card_id", "virtual_card_credentials", ["card_id"])
    op.create_index("ix_virtual_card_credentials_card_number", "virtual_card_credentials", ["card_number"], unique=True)
    op.add_column("user_cards", sa.Column("virtual_credential_id", sa.Integer(), nullable=True))
    op.create_index("ix_user_cards_virtual_credential_id", "user_cards", ["virtual_credential_id"])
    op.create_foreign_key(
        "fk_user_cards_virtual_credential_id",
        "user_cards",
        "virtual_card_credentials",
        ["virtual_credential_id"],
        ["id"],
        ondelete="SET NULL",
    )
