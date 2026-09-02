from loguru import logger

from src.domains.shifts.queries.get_shifts_in_date_range.query import (
    GetShiftsInDateRangeQuery,
)
from src.domains.shifts.query_models import PaginatedQueryModel, ShiftQueryModel
from src.domains.shifts.query_repository import QueryShiftRepository

class GetShiftsInDateRangeQueryHandler:
    def __init__(self, repository: QueryShiftRepository):
        self._repository = repository

    async def handle(
        self,
        query: GetShiftsInDateRangeQuery,
    ) -> PaginatedQueryModel[ShiftQueryModel]:
        output = await self._repository.get_by_date_range(
            start_date=query.start,
            end_date=query.end,
            reference_id=query.reference_id,
            approved=query.approved,
            automatically_closed=query.automatically_closed,
            is_open=query.is_open,
            sort_direction=query.sort_direction,
            limit=query.limit,
            offset=query.offset,
        )
        logger.debug(
            "Shift date-range query handled result_count={} total={}",
            len(output.items),
            output.total,
        )
        return output
