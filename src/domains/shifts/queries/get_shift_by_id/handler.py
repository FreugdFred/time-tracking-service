from loguru import logger

from src.domains.shifts.queries.get_shift_by_id.query import GetShiftByIdQuery
from src.domains.shifts.query_models import ShiftQueryModel
from src.domains.shifts.query_repository import QueryShiftRepository
from src.exceptions import NotFoundException

class GetShiftByIdQueryHandler:
    def __init__(self, repository: QueryShiftRepository):
        self._repository = repository

    async def handle(self, query: GetShiftByIdQuery) -> ShiftQueryModel:
        output = await self._repository.get(query.id)

        if output is None:
            logger.warning("Shift query returned no result shift_id={}", query.id)
            raise NotFoundException(model=ShiftQueryModel, identifier=str(query.id))

        logger.debug("Shift query completed shift_id={}", query.id)
        return output
