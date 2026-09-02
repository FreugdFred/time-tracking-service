from loguru import logger

from src.core.handler_base import HandlerBase
from src.domains.pauses.commands.remove_pause.command import RemovePauseCommand
from src.domains.shifts.command_repository import CommandShiftRepository


class RemovePauseCommandHandler(HandlerBase):
    def __init__(self, shift_repository: CommandShiftRepository) -> None:
        self._shift_repository = shift_repository

    async def handle(self, command: RemovePauseCommand) -> None:
        shift = await self._shift_repository.get_by_pause_id(command.id)
        if shift is None:
            logger.debug(
                "Remove pause command skipped; pause not found pause_id={}",
                command.id,
            )
            return

        shift.delete_pause(command.id)
        await self._shift_repository.save(shift)
        logger.info(
            "Remove pause command completed pause_id={} shift_id={}",
            command.id,
            shift.id,
        )
        await self.publish_events(shift.pull_events())
