"""Bring user_cards / virtual_card_credentials in line with the ORM models.

The DB predates the virtual-card-vault refactor: it lacks the
virtual_card_credentials table and the user_cards.virtual_credential_id
column, so the card-list query fails with UndefinedColumn.

This creates the missing table and adds the missing nullable FK column so
reads succeed. Existing rows keep virtual_credential_id = NULL (card_number_last4
is already stored on user_cards, so the wallet still renders).

Run:  python -m scripts.fix_user_cards_schema
"""

from sqlalchemy import inspect, text

from app.core.database import engine
from app.models.virtual_card_credential import VirtualCardCredential


def main() -> None:
    inspector = inspect(engine)

    # 1) Create the vault table if it does not exist (matches the model exactly).
    if "virtual_card_credentials" not in inspector.get_table_names():
        print("[+] CREATE TABLE virtual_card_credentials")
        VirtualCardCredential.__table__.create(bind=engine, checkfirst=True)
    else:
        print("[=] virtual_card_credentials already exists")

    # 2) Add user_cards.virtual_credential_id (+ index + FK) if missing.
    inspector = inspect(engine)  # refresh after possible DDL above
    user_cards_cols = {c["name"] for c in inspector.get_columns("user_cards")}

    with engine.begin() as conn:
        if "virtual_credential_id" not in user_cards_cols:
            print("[+] ALTER user_cards ADD COLUMN virtual_credential_id")
            conn.execute(text(
                "ALTER TABLE user_cards "
                "ADD COLUMN IF NOT EXISTS virtual_credential_id integer"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_user_cards_virtual_credential_id "
                "ON user_cards (virtual_credential_id)"
            ))
            conn.execute(text(
                "ALTER TABLE user_cards "
                "ADD CONSTRAINT fk_user_cards_virtual_credential_id "
                "FOREIGN KEY (virtual_credential_id) "
                "REFERENCES virtual_card_credentials (id) ON DELETE SET NULL"
            ))
        else:
            print("[=] user_cards.virtual_credential_id already exists")

    print("[OK] user_cards schema matches the model.")


if __name__ == "__main__":
    main()
