from zoneinfo import ZoneInfo

import nats
from nats.aio.client import Client as NatsClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from dependency_container import Dependency
from src.core.database import create_database_engine, create_session_factory
from src.core.settings import Settings
from time_provider import AbstractTimeProvider, TimeProvider


def include_core_dependencies(settings: Settings | None = None) -> None:
    if settings is None:
        settings = Settings()  # pyright: ignore[reportCallIssue]

    Dependency.register_instance(Settings, settings)

    local_timezone = ZoneInfo(settings.LOCAL_TIMEZONE)
    Dependency.register_instance(
        AbstractTimeProvider,
        TimeProvider(local_timezone=local_timezone),
    )

    engine = create_database_engine(str(settings.DATABASE_URL))
    Dependency.register_instance(AsyncEngine, engine)
    Dependency.register_factory(AsyncSession, create_session_factory(engine))


async def include_nats_dependency(settings: Settings) -> NatsClient | None:
    if settings.NATS_URL is None:
        return None

    nats_client = await nats.connect(str(settings.NATS_URL))
    Dependency.register_instance(NatsClient, nats_client)
    return nats_client
