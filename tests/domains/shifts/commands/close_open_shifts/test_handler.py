from datetime import UTC, datetime

from dependency_container import Dependency
from src.core.unit_of_work import UnitOfWork
from src.domains.pauses.entity import PauseEntity
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.close_open_shifts.command import (
    CloseOpenShiftsCommand,
)
from src.domains.shifts.commands.close_open_shifts.handler import (
    CloseOpenShiftsCommandHandler,
)
from src.domains.shifts.entity import ShiftEntity
from time_provider import FakeTimeProvider


NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


async def test_closes_expired_shift_and_its_active_pause(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    time_provider.travel(NOW)
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 22, tzinfo=UTC),
    )
    pause = PauseEntity(
        shift_id=shift.id,
        started_at=datetime(2026, 9, 2, 9, tzinfo=UTC),
    )
    shift.pauses.append(pause)
    async with UnitOfWork() as session:
        await command_shift_repository.save(session, shift)

    await Dependency.get(CloseOpenShiftsCommandHandler).handle(
        CloseOpenShiftsCommand(close_after_hours=12)
    )

    async with UnitOfWork() as session:
        saved_shift = await command_shift_repository.get(session, shift.id)

    assert saved_shift is not None
    assert saved_shift.finished_at == NOW
    assert saved_shift.pauses[0].finished_at == NOW
    assert saved_shift.automatically_closed


async def test_does_nothing_when_no_shift_has_expired(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    time_provider.travel(NOW)

    await Dependency.get(CloseOpenShiftsCommandHandler).handle(
        CloseOpenShiftsCommand(close_after_hours=12)
    )

    async with UnitOfWork() as session:
        shifts = await command_shift_repository.get_open_started_at_or_before(
            session,
            NOW,
        )
    assert shifts == []
