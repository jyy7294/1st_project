from sqlalchemy import inspect

from app.core.database import engine


def main() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    print("현재 DB 테이블:")

    for table_name in sorted(table_names):
        print(f"- {table_name}")

    required_tables = {
        "cards",
        "card_benefits",
        "merchant_aliases",
    }

    missing_tables = required_tables - set(table_names)

    if missing_tables:
        print("\n누락된 테이블:")
        for table_name in sorted(missing_tables):
            print(f"- {table_name}")
    else:
        print("\n필수 테이블 생성 완료")


if __name__ == "__main__":
    main()