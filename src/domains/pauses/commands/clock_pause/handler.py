from uuid import UUID

from loguru import logger

from src.core.handler_base import HandlerBase
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
        shift = await self._shift_repository.get_active(command.reference_id)
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

        await self._shift_repository.save(shift)
        logger.info(
            "Pause clock command completed action={} pause_id={} shift_id={}",
            action,
            pause.id,
            shift.id,
        )
        await self.publish_events(shift.pull_events())
        return pause.id
