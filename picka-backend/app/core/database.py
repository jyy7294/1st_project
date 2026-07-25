from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


LOCAL_DATABASE_HOSTS = {None, "localhost", "127.0.0.1", "::1"}


def database_url_with_required_ssl(
    database_url: str,
    *,
    sslmode: str = "require",
    sslrootcert: str | None = None,
) -> URL:
    url = make_url(database_url)
    if (
        url.drivername.startswith("postgresql")
        and url.host not in LOCAL_DATABASE_HOSTS
    ):
        if sslmode not in {"require", "verify-ca", "verify-full"}:
            raise ValueError("DATABASE_SSLMODE must be require, verify-ca, or verify-full")
        query = {"sslmode": sslmode}
        if sslrootcert:
            query["sslrootcert"] = sslrootcert
        return url.update_query_dict(query)
    return url


engine = create_engine(
    database_url_with_required_ssl(
        settings.database_url,
        sslmode=settings.database_sslmode,
        sslrootcert=settings.database_sslrootcert,
    ),
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
