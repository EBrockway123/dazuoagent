"""SQLAlchemy engine, session factory, and FastAPI dependency.

Sync engine for now (SQLite doesn't need async; async gives little benefit on
local file DBs and complicates pytest fixtures). When migrating to PostgreSQL,
swap `create_engine` → `create_async_engine` and update the `get_db` dependency.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from dazuoagent.core.config import settings


class Base(DeclarativeBase):
    """Single declarative base shared by every ORM model."""


engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    # SQLite needs this when used across threads (uvicorn workers, tests).
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency. Always use `with`-style close via try/finally."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Used by the seed script and by tests.

    Real migrations go through Alembic (see `alembic/` once introduced). For
    the framework scaffold, `Base.metadata.create_all(engine)` is enough.
    """
    # Importing here avoids a circular import: models import Base from here.
    from dazuoagent import models  # noqa: F401  -- registers all mappers

    Base.metadata.create_all(bind=engine)