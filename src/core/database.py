from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool


def create_database_engine(
    database_url: str,
) -> AsyncEngine:
    options: dict[str, Any] = {"echo": False}
    if make_url(database_url).get_backend_name() == "sqlite":
        options["poolclass"] = NullPool
    return create_async_engine(database_url, **options)


def create_session_factory(engine: AsyncEngine) -> Callable[[], AsyncSession]:
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=True,
    )

    def create_session() -> AsyncSession:
        return session_factory()

    return create_session
