from dependency_container import Dependency

from src.core.unit_of_work import UnitOfWork
from src.jobs.publish_events import publish_events
from messaging.commands.repository import CommandMessagingRepository
from src.messaging.entity import BaseDomainEvent
from messaging.queries.repository import QueryMessagingRepository


async def test_does_not_publish_events_when_nats_is_not_configured() -> None:
    async with UnitOfWork() as session:
        await Dependency.get(CommandMessagingRepository).save_many(
            session,
            [BaseDomainEvent(reference_id="employee-1")],
        )

    await publish_events()

    events = await Dependency.get(QueryMessagingRepository).list_unpublished()
    assert len(events) == 1
