import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from dependency_container import Dependency
from src.core.base import Base, import_all_database_models
from src.core.di import include_core_dependencies
from src.core.settings import Settings
from src.domains.pauses.di import include_pause_dependencies
from src.domains.pauses.query_repository import QueryPauseRepository
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.di import include_shift_dependencies
from src.domains.shifts.query_repository import QueryShiftRepository
from time_provider import AbstractTimeProvider, FakeTimeProvider

DEFAULT_NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)

import_all_database_models()


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def configure_dependencies(tmp_path: Path) -> Iterator[None]:
    database_path = (tmp_path / "test.db").resolve()
    sqlite_path = database_path.as_posix()
    settings = Settings.model_validate(
        {"DATABASE_URL": f"sqlite+aiosqlite:///{sqlite_path}"}
    )

    Dependency.clear()
    include_core_dependencies(settings)
    include_shift_dependencies()
    include_pause_dependencies()
    Dependency.overwrite(
        AbstractTimeProvider,
        FakeTimeProvider(
            local_timezone=ZoneInfo("Europe/Amsterdam"),
            time=DEFAULT_NOW,
            freeze=True,
        ),
    )
    engine = Dependency.get(AsyncEngine)
    asyncio.run(create_schema(engine))

    yield

    Dependency.clear()
    asyncio.run(engine.dispose())


@pytest.fixture
def time_provider() -> FakeTimeProvider:
    provider = Dependency.get(AbstractTimeProvider)
    assert isinstance(provider, FakeTimeProvider)
    return provider


@pytest.fixture
def command_shift_repository() -> CommandShiftRepository:
    return Dependency.get(CommandShiftRepository)


@pytest.fixture
def query_shift_repository() -> QueryShiftRepository:
    return Dependency.get(QueryShiftRepository)


@pytest.fixture
def query_pause_repository() -> QueryPauseRepository:
    return Dependency.get(QueryPauseRepository)
