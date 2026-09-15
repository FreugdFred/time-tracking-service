from datetime import UTC, datetime
from uuid import uuid4

from dependency_container import Dependency
from src.core.unit_of_work import UnitOfWork
from src.domains.pauses.commands.remove_pause.command import RemovePauseCommand
from src.domains.pauses.commands.remove_pause.handler import RemovePauseCommandHandler
from src.domains.pauses.entity import PauseEntity
from domains.shifts.commands.repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from time_provider import FakeTimeProvider


async def test_remove_missing_pause_is_successful_no_op(
    command_shift_repository: CommandShiftRepository,
) -> None:
    pause_id = uuid4()

    await Dependency.get(RemovePauseCommandHandler).handle(
        RemovePauseCommand(id=pause_id)
    )

    async with UnitOfWork() as session:
        shift = await command_shift_repository.get_by_pause_id(session, pause_id)
    assert shift is None


async def test_remove_deletes_pause_through_its_shift(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    shift = ShiftEntity(
        id=pause.shift_id,
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 17, tzinfo=UTC),
        pauses=[pause],
    )
    async with UnitOfWork() as session:
        await command_shift_repository.save(session, shift)

    await Dependency.get(RemovePauseCommandHandler).handle(
        RemovePauseCommand(id=pause.id)
    )

    async with UnitOfWork() as session:
        saved_shift = await command_shift_repository.get(session, shift.id)

    assert saved_shift is not None
    assert saved_shift.pauses == []
