from datetime import UTC, datetime
from uuid import uuid4

from dependency_container import Dependency
from pydantic import NatsDsn
from src.core.settings import Settings
from src.core.unit_of_work import UnitOfWork
from src.domains.pauses.entity import PauseEntity
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.clock_shift.command import ClockShiftCommand
from src.domains.shifts.commands.clock_shift.handler import ClockShiftCommandHandler
from src.domains.shifts.entity import ShiftEntity
from src.messaging.query_repository import QueryMessagingRepository
from time_provider import FakeTimeProvider


NOW = datetime(2026, 9, 2, 10, tzinfo=UTC)


async def test_starts_shift_when_none_is_active(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
    query_messaging_repository: QueryMessagingRepository,
) -> None:
    settings = Dependency.get(Settings)
    settings.NATS_URL = NatsDsn("nats://localhost:4222")
    time_provider.travel(NOW)
    handler = Dependency.get(ClockShiftCommandHandler)

    shift_id = await handler.handle(ClockShiftCommand(reference_id="employee-1"))

    async with UnitOfWork() as session:
        saved_shift = await command_shift_repository.get(session, shift_id)

    assert saved_shift is not None
    assert saved_shift.id == shift_id
    assert saved_shift.reference_id == "employee-1"
    assert saved_shift.started_at == NOW
    assert saved_shift.finished_at is None

    events = await query_messaging_repository.list_unpublished()
    assert {(event.type, event.subject) for event in events} == {
        ("ShiftCreatedEvent", "employee-1"),
        ("ShiftStartedEvent", "employee-1"),
    }


async def test_does_not_store_events_when_nats_is_not_configured(
    time_provider: FakeTimeProvider,
    query_messaging_repository: QueryMessagingRepository,
) -> None:
    time_provider.travel(NOW)

    await Dependency.get(ClockShiftCommandHandler).handle(
        ClockShiftCommand(reference_id="employee-1")
    )

    assert await query_messaging_repository.list_unpublished() == []


async def test_finishes_active_shift_and_pause(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    time_provider.travel(NOW)
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        pauses=[
            PauseEntity(
                shift_id=uuid4(),
                started_at=datetime(2026, 9, 2, 9, tzinfo=UTC),
            )
        ],
    )
    shift.pauses[0].shift_id = shift.id

    async with UnitOfWork() as session:
        await command_shift_repository.save(session, shift)

    shift_id = await Dependency.get(ClockShiftCommandHandler).handle(
        ClockShiftCommand(reference_id=shift.reference_id)
    )

    async with UnitOfWork() as session:
        saved_shift = await command_shift_repository.get(session, shift_id)

    assert saved_shift is not None
    assert saved_shift.finished_at == NOW
    assert saved_shift.pauses[0].finished_at == NOW
