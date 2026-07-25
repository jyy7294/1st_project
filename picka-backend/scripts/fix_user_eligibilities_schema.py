"""Bring the user_eligibilities table in line with the ORM model.

Adds any columns the model expects but the DB is missing, so the daily
recommendation scheduler stops failing with UndefinedColumn.

Run:  python -m scripts.fix_user_eligibilities_schema
"""

from sqlalchemy import inspect, text

from app.core.database import engine

TABLE = "user_eligibilities"

# column_name -> ALTER ... ADD COLUMN clause (IF NOT EXISTS handled per-column)
REQUIRED_COLUMNS = {
    "eligibility_value": "varchar(255) NOT NULL DEFAULT ''",
    "verification_status": "varchar(30) NOT NULL DEFAULT 'unverified'",
    "verified_at": "timestamptz",
    "expires_at": "timestamptz",
}


def main() -> None:
    inspector = inspect(engine)

    if TABLE not in inspector.get_table_names():
        print(f"[!] Table '{TABLE}' does not exist. Run: alembic upgrade head")
        return

    existing = {col["name"] for col in inspector.get_columns(TABLE)}
    print(f"[i] Existing columns: {sorted(existing)}")

    missing = {c: d for c, d in REQUIRED_COLUMNS.items() if c not in existing}
    if not missing:
        print("[OK] Schema already matches the model. Nothing to do.")
        return

    with engine.begin() as conn:
        for col, ddl in missing.items():
            stmt = f'ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS {col} {ddl}'
            print(f"[+] {stmt}")
            conn.execute(text(stmt))

    print(f"[OK] Added: {sorted(missing)}")


if __name__ == "__main__":
    main()
