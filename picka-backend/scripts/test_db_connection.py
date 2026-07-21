from sqlalchemy import text

from app.core.database import engine


def test_connection() -> None:
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar_one()

        print("DB 연결 성공:", value)

    except Exception as error:
        print("DB 연결 실패")
        print(type(error).__name__)
        print(error)


if __name__ == "__main__":
    test_connection()