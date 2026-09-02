from uuid import UUID

from loguru import logger

from src.core.handler_base import HandlerBase
from src.domains.pauses.commands.save_pause.command import SavePauseCommand
from src.domains.pauses.entity import PauseEntity
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import UnfinishedException, ValidationException, NotFoundException


class SavePauseCommandHandler(HandlerBase):
    def __init__(self, shift_repository: CommandShiftRepository) -> None:
        self._shift_repository = shift_repository

    async def handle(self, command: SavePauseCommand) -> UUID:
        shift = await self._shift_repository.get_by_pause_id(command.id)

        if shift is None:
            shift = await self._create_pause(command)
            operation = "created"
        else:
            self._update_pause(shift, command)
            operation = "updated"

        await self._shift_repository.save(shift)
        logger.info(
            "Save pause command completed operation={} pause_id={} shift_id={}",
            operation,
            command.id,
            shift.id,
        )
        await self.publish_events(shift.pull_events())
        return command.id

    async def _create_pause(self, command: SavePauseCommand) -> ShiftEntity:
        required_fields = {
            "shift_id": command.shift_id,
            "started_at": command.started_at,
            "finished_at": command.finished_at,
        }
        missing_fields = [
            name for name, value in required_fields.items() if value is None
        ]
        if missing_fields:
            raise ValidationException(
                f"Cannot create pause {command.id}: missing required fields: "
                f"{', '.join(missing_fields)}."
            )

        assert command.shift_id is not None
        assert command.started_at is not None
        assert command.finished_at is not None

        shift = await self._shift_repository.get(command.shift_id)
        if shift is None:
            logger.warning(
                "Save pause command rejected; shift not found "
                "pause_id={} shift_id={}",
                command.id,
                command.shift_id,
            )
            raise NotFoundException(ShiftEntity, str(command.shift_id))

        shift.add_pause(
            PauseEntity(
                id=command.id,
                shift_id=command.shift_id,
                started_at=command.started_at,
                finished_at=command.finished_at,
            )
        )
        return shift

    @staticmethod
    def _update_pause(shift: ShiftEntity, command: SavePauseCommand) -> None:
        if command.shift_id is not None and command.shift_id != shift.id:
            raise ValidationException("A pause cannot be moved to another shift.")

        if command.started_at is None and command.finished_at is None:
            return

        pause = shift.get_pause(command.id)
        if pause.finished_at is None:
            raise UnfinishedException(PauseEntity, str(pause.id))

        started_at = (
            command.started_at
            if command.started_at is not None
            else pause.started_at
        )
        finished_at = (
            command.finished_at
            if command.finished_at is not None
            else pause.finished_at
        )
        shift.change_pause_time_range(
            pause.id,
            started_at=started_at,
            finished_at=finished_at,
        )
