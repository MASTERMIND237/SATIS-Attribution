import os
from typing import Any

from sqlmodel import SQLModel, Session, create_engine


DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_CONNECT_TIMEOUT = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "5"))


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _engine_kwargs(url: str) -> dict[str, Any]:
    normalized_url = normalize_database_url(url)
    kwargs: dict[str, Any] = {"echo": False, "pool_pre_ping": True}

    if normalized_url.startswith("postgresql"):
        kwargs["connect_args"] = {"connect_timeout": DATABASE_CONNECT_TIMEOUT}

    return kwargs


def build_engine(url: str):
    if not url:
        raise RuntimeError("DATABASE_URL is required and must point to your Supabase Postgres database.")

    normalized_url = normalize_database_url(url)
    return create_engine(normalized_url, **_engine_kwargs(normalized_url))


primary_engine = build_engine(DATABASE_URL)
engine = primary_engine
database_state = {
    "configured_url": normalize_database_url(DATABASE_URL),
    "active_url": normalize_database_url(DATABASE_URL),
    "last_error": None,
}


def get_session():
    with Session(engine) as session:
        yield session


def initialize_database():
    global engine

    SQLModel.metadata.create_all(primary_engine)
    engine = primary_engine
    database_state["active_url"] = normalize_database_url(DATABASE_URL)
    database_state["last_error"] = None
    return database_state


def get_database_state() -> dict[str, Any]:
    return dict(database_state)
