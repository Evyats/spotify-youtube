import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/spotify_youtube")


def make_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)


def make_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=make_engine())


def get_db(session_local: sessionmaker) -> Generator[Session, None, None]:
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def should_auto_create_schema() -> bool:
    return os.getenv("DB_AUTO_CREATE", "0").lower() in {"1", "true", "yes", "on"}
