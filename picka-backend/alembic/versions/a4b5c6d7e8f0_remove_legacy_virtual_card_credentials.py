"""remove legacy plaintext virtual card credentials

Revision ID: a4b5c6d7e8f0
Revises: a3b4c5d6e7f8
Create Date: 2026-07-27

This is an idempotent schema-drift cleanup. The original security migration
already removed these objects on clean databases, but they remained in the
deployed Supabase schema after a legacy restore.
"""

from collections.abc import Sequence

from alembic import op


revision: str = "a4b5c6d7e8f0"
down_revision: str | None = "a3b4c5d6e7f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE user_cards "
        "DROP CONSTRAINT IF EXISTS fk_user_cards_virtual_credential_id"
    )
    op.execute("DROP INDEX IF EXISTS ix_user_cards_virtual_credential_id")
    op.execute(
        "ALTER TABLE user_cards DROP COLUMN IF EXISTS virtual_credential_id"
    )
    op.execute("DROP TABLE IF EXISTS virtual_card_credentials")


def downgrade() -> None:
    # Intentionally irreversible: restoring columns for plaintext card number,
    # CVC, expiry, and password fragments would violate the token-only boundary.
    pass
