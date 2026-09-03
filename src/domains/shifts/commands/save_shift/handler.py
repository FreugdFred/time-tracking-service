from uuid import UUID

from loguru import logger

from src.core.handler_base import HandlerBase
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.save_shift.command import SaveShiftCommand
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import OverlappingException, ValidationException


class SaveShiftCommandHandler(HandlerBase):
    def __init__(self, shift_repository: CommandShiftRepository):
        self._shift_repository = shift_repository

    async def handle(self, command: SaveShiftCommand) -> UUID:
        existing_shift = await self._shift_repository.get(command.id)

        if existing_shift is not None:
            shift = self._update_entity(existing_shift, command)
            operation = "updated"
        else:
            shift = self._create_entity(command)
            operation = "created"

        if await self._shift_repository.has_overlap(shift):
            logger.warning(
                "Save shift command rejected due to overlap shift_id={}",
                shift.id,
            )
            raise OverlappingException(
                ShiftEntity,
                identifier=str(shift.id),
                start=shift.started_at,
                end=shift.finished_at,
            )

        shift_id = await self._shift_repository.save(shift)
        logger.info(
            "Save shift command completed operation={} shift_id={}",
            operation,
            shift_id,
        )
        await self.publish_events(shift.pull_events())
        return shift_id

    @staticmethod
    def _update_entity(shift: ShiftEntity, command: SaveShiftCommand) -> ShiftEntity:
        if command.reference_id:
            shift.reference_id = command.reference_id

        if command.started_at is not None or command.finished_at is not None:
            shift.change_time_range(
                started_at=command.started_at,
                finished_at=command.finished_at,
            )

        if "automatically_closed" in command.model_fields_set:
            shift.automatically_closed = command.automatically_closed

        if "approved" in command.model_fields_set and command.approved:
            shift.approve()

        if "approved" in command.model_fields_set and not command.approved:
            shift.disapprove()

        return shift

    @staticmethod
    def _create_entity(command: SaveShiftCommand) -> ShiftEntity:
        required_fields = {
            "reference_id": command.reference_id,
            "started_at": command.started_at,
            "finished_at": command.finished_at,
        }
        missing_fields = [
            name for name, value in required_fields.items() if not value
        ]
        if missing_fields:
            raise ValidationException(
                f"Cannot create shift {command.id}: missing required fields: "
                f"{', '.join(missing_fields)}."
            )

        assert command.started_at
        assert command.reference_id

        return ShiftEntity.create(
            id=command.id,
            reference_id=command.reference_id,
            started_at=command.started_at,
            finished_at=command.finished_at,
            automatically_closed=command.automatically_closed,
            approved=command.approved,
        )
