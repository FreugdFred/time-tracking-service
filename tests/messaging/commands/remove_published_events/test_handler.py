from datetime import UTC, datetime
from uuid import UUID, uuid4

from dependency_container import Dependency
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.unit_of_work import UnitOfWork
from src.messaging.commands.remove_published_events.command import (
    RemovePublishedEventsCommand,
)
from src.messaging.commands.remove_published_events.handler import (
    RemovePublishedEventsCommandHandler,
)
from src.messaging.models import DbEvent
from time_provider import FakeTimeProvider


NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


async def save_events(*events: DbEvent) -> None:
    async with UnitOfWork() as session:
        session.add_all(events)


async def list_event_ids() -> set[UUID]:
    async with Dependency.get(AsyncSession) as session:
        return set(await session.scalars(select(DbEvent.id)))


async def test_removes_events_published_at_or_before_retention_cutoff(
    time_provider: FakeTimeProvider,
) -> None:
    time_provider.travel(NOW)
    older_id = uuid4()
    boundary_id = uuid4()
    recent_id = uuid4()
    await save_events(
        DbEvent(
            id=older_id,
            type="shift.started",
            subject="shift",
            data={},
            published_at=datetime(2026, 9, 2, 11, 49, 59, tzinfo=UTC),
        ),
        DbEvent(
            id=boundary_id,
            type="shift.started",
            subject="shift",
            data={},
            published_at=datetime(2026, 9, 2, 11, 50, tzinfo=UTC),
        ),
        DbEvent(
            id=recent_id,
            type="shift.started",
            subject="shift",
            data={},
            published_at=datetime(2026, 9, 2, 11, 50, 1, tzinfo=UTC),
        ),
    )

    await Dependency.get(RemovePublishedEventsCommandHandler).handle(
        RemovePublishedEventsCommand(retention_minutes=10)
    )

    assert await list_event_ids() == {recent_id}


async def test_keeps_unpublished_events_past_retention_cutoff(
    time_provider: FakeTimeProvider,
) -> None:
    time_provider.travel(NOW)
    unpublished_id = uuid4()
    await save_events(
        DbEvent(
            id=unpublished_id,
            type="shift.started",
            subject="shift",
            data={},
            occurred_at=datetime(2026, 9, 2, 11, 40, tzinfo=UTC),
            published_at=None,
        )
    )

    await Dependency.get(RemovePublishedEventsCommandHandler).handle(
        RemovePublishedEventsCommand(retention_minutes=10)
    )

    assert await list_event_ids() == {unpublished_id}
