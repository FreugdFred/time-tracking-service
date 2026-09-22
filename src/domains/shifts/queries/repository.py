from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dependency_container import Dependency
from src.domains.shifts.models import DbShift
from src.domains.shifts.query_models import (
    PaginatedQueryModel,
    ShiftByReferenceIdQueryModel,
    ShiftQueryModel,
)


class QueryShiftRepository:
    async def get_by_reference_id(
        self,
        reference_id: str,
        *,
        approved: bool | None = None,
        automatically_closed: bool | None = None,
        is_open: bool | None = None,
        sort_direction: Literal["asc", "desc"] = "desc",
        limit: int,
        offset: int,
    ) -> PaginatedQueryModel[ShiftByReferenceIdQueryModel]:
        filters = [DbShift.reference_id == reference_id]
        if approved is not None:
            filters.append(DbShift.approved.is_(approved))
        if automatically_closed is not None:
            filters.append(DbShift.automatically_closed.is_(automatically_closed))
        if is_open is not None:
            filters.append(
                DbShift.finished_at.is_(None)
                if is_open
                else DbShift.finished_at.is_not(None)
            )

        order = asc if sort_direction == "asc" else desc
        order_by = (
            order(DbShift.started_at),
            order(DbShift.created_at),
            order(DbShift.id),
        )
        query = (
            select(DbShift)
            .where(*filters)
            .options(selectinload(DbShift.pauses))
            .order_by(*order_by)
            .limit(limit)
            .offset(offset)
        )
        count_query = select(func.count(DbShift.id)).where(*filters)

        async with Dependency.get(AsyncSession) as session:
            total = await session.scalar(count_query)
            result = await session.scalars(query)
            items = [
                ShiftByReferenceIdQueryModel.model_validate(shift)
                for shift in result.all()
            ]

            return PaginatedQueryModel[ShiftByReferenceIdQueryModel](
                items=items,
                total=total or 0,
                limit=limit,
                offset=offset,
            )

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        reference_id: str | None = None,
        *,
        approved: bool | None = None,
        automatically_closed: bool | None = None,
        is_open: bool | None = None,
        sort_direction: Literal["asc", "desc"] = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedQueryModel[ShiftQueryModel]:
        filters = [
            DbShift.started_at <= end_date,
            or_(DbShift.finished_at.is_(None), DbShift.finished_at >= start_date),
        ]
        if reference_id is not None:
            filters.append(DbShift.reference_id == reference_id)
        if approved is not None:
            filters.append(DbShift.approved.is_(approved))
        if automatically_closed is not None:
            filters.append(DbShift.automatically_closed.is_(automatically_closed))
        if is_open is not None:
            filters.append(
                DbShift.finished_at.is_(None)
                if is_open
                else DbShift.finished_at.is_not(None)
            )

        order = asc if sort_direction == "asc" else desc
        order_by = (
            order(DbShift.started_at),
            order(DbShift.created_at),
            order(DbShift.id),
        )

        query = (
            select(DbShift)
            .where(*filters)
            .options(selectinload(DbShift.pauses))
            .order_by(*order_by)
            .limit(limit)
            .offset(offset)
        )
        count_query = select(func.count(DbShift.id)).where(*filters)

        async with Dependency.get(AsyncSession) as session:
            total = await session.scalar(count_query)
            result = await session.scalars(query)
            items = [
                ShiftQueryModel.model_validate(shift) for shift in result.all()
            ]

            return PaginatedQueryModel[ShiftQueryModel](
                items=items,
                total=total or 0,
                limit=limit,
                offset=offset,
            )

    async def get(self, id: UUID) -> ShiftQueryModel | None:
        async with Dependency.get(AsyncSession) as session:
            db_shift = await session.get(
                DbShift,
                id,
                options=(selectinload(DbShift.pauses),),
            )

            return ShiftQueryModel.model_validate(db_shift) if db_shift else None
