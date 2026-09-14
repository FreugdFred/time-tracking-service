from uuid import UUID

from loguru import logger

from src.core.handler_base import HandlerBase
from src.core.unit_of_work import UnitOfWork
from src.domains.pauses.commands.clock_pause.command import ClockPauseCommand
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import NotFoundException
from time_provider import AbstractTimeProvider


class ClockPauseCommandHandler(HandlerBase):
    def __init__(
        self,
        shift_repository: CommandShiftRepository,
        time_provider: AbstractTimeProvider,
    ) -> None:
        self._shift_repository = shift_repository
        self._time_provider = time_provider

    async def handle(self, command: ClockPauseCommand) -> UUID:
        now = self._time_provider.now()
        async with UnitOfWork() as session:
            shift = await self._shift_repository.get_active(
                session,
                command.reference_id,
            )
            if shift is None:
                logger.warning(
                    "Clock pause command rejected; active shift not found "
                    "reference_id={}",
                    command.reference_id,
                )
                raise NotFoundException(
                    ShiftEntity,
                    command.reference_id,
                    detail=(
                        "Cannot clock a pause because no active shift was found for "
                        f"reference '{command.reference_id}'. Start a shift first."
                    ),
                )

            if shift.active_pause is None:
                pause = shift.start_pause(now)
                action = "started"
            else:
                pause = shift.finish_pause(now)
                action = "finished"

            await self._shift_repository.save(session, shift)
            await self.save_events(session, shift.pull_events())

        logger.info(
            "Pause clock command completed action={} pause_id={} shift_id={}",
            action,
            pause.id,
            shift.id,
        )
        return pause.id
