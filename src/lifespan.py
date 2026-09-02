from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncEngine

from dependency_container import Dependency
from src.core.base import import_all_database_models
from src.core.di import include_nats_dependency
from src.core.settings import Settings
from src.jobs.configure_scheduler import scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    import_all_database_models()

    settings = Dependency.get(Settings)
    nats_client = await include_nats_dependency(settings)

    scheduler.start()
    logger.info("Application startup completed")

    try:
        yield

    finally:
        logger.info("Application shutdown started")
        scheduler.shutdown(wait=True)

        if nats_client is not None:
            await nats_client.drain()
            ''
        await Dependency.get(AsyncEngine).dispose()
        logger.info("Application shutdown completed")
