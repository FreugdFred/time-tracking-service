import json
from datetime import UTC, datetime
from uuid import uuid4

from dependency_container import Dependency

from tests.fakes.nats_recording_client import RecordingNatsClient
from src.core.settings import Settings
from src.core.unit_of_work import UnitOfWork
from src.domains.shifts.events import ShiftStartedEvent
from src.jobs.publish_events import publish_events
from src.messaging.commands.repository import CommandMessagingRepository
from src.messaging.entity import BaseDomainEvent
from src.messaging.event_publisher import EventPublisher
from src.messaging.queries.repository import QueryMessagingRepository



async def test_does_not_publish_events_when_nats_is_not_configured() -> None:
    async with UnitOfWork() as session:
        await Dependency.get(CommandMessagingRepository).save_many(
            session,
            [BaseDomainEvent(reference_id="employee-1")],
        )

    await publish_events()

    events = await Dependency.get(QueryMessagingRepository).list_unpublished()
    assert len(events) == 1


async def test_publishes_event_envelope() -> None:
    command_repository = Dependency.get(CommandMessagingRepository)
    query_repository = Dependency.get(QueryMessagingRepository)
    occurrence_datetime = datetime(2026, 9, 3, 9, 15, tzinfo=UTC)
    shift_id = uuid4()

    async with UnitOfWork() as session:
        await command_repository.save_many(
            session,
            [
                ShiftStartedEvent(
                    reference_id="employee-123",
                    occurrence_datetime=occurrence_datetime,
                    shift_id=shift_id,
                    started_at=occurrence_datetime,
                )
            ],
        )

    events = await query_repository.list_unpublished()
    assert len(events) == 1

    nats_client = RecordingNatsClient()
    publisher = EventPublisher(
        command_repository=command_repository,
        query_repository=query_repository,
        settings=Dependency.get(Settings),
        nats_client=nats_client,
    )

    await publisher.publish()

    assert len(nats_client.messages) == 1
    subject, payload = nats_client.messages[0]
    assert subject == "Time-Tracking-Service-API.ShiftStartedEvent"
    assert json.loads(payload) == {
        "id": str(events[0].id),
        "type": "ShiftStartedEvent",
        "subject": "employee-123",
        "occurrence_datetime": "2026-09-03T09:15:00Z",
        "data": {
            "shift_id": str(shift_id),
            "started_at": "2026-09-03T09:15:00Z",
        },
    }
    assert await query_repository.list_unpublished() == []
