from loguru import logger

from src.domains.shifts.queries.get_shifts_by_reference_id.query import (
    GetShiftsByReferenceIdQuery,
)
from src.domains.shifts.query_models import (
    PaginatedQueryModel,
    ShiftByReferenceIdQueryModel,
)
from src.domains.shifts.query_repository import QueryShiftRepository

class GetShiftsByReferenceIdQueryHandler:
    def __init__(self, repository: QueryShiftRepository):
        self._repository = repository

    async def handle(
        self,
        query: GetShiftsByReferenceIdQuery,
    ) -> PaginatedQueryModel[ShiftByReferenceIdQueryModel]:
        output = await self._repository.get_by_reference_id(
            query.reference_id,
            approved=query.approved,
            automatically_closed=query.automatically_closed,
            is_open=query.is_open,
            sort_direction=query.sort_direction,
            limit=query.limit,
            offset=query.offset,
        )
        logger.debug(
            "Shift reference query handled result_count={} total={}",
            len(output.items),
            output.total,
        )
        return output
