from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dependency_container import Dependency
from src.domains.pauses.models import DbPause
from src.domains.shifts.entity import ShiftEntity
from src.domains.shifts.mapper import ShiftMapper
from src.domains.shifts.models import DbShift
from src.exceptions import OverlappingException


class CommandShiftRepository:
    DEFAULT_SHIFT_ORDER_BY = (DbShift.started_at.desc(), DbShift.created_at.desc())

    async def get_active(self, reference_id: str) -> ShiftEntity | None:
        async with Dependency.get(AsyncSession) as session:
            query = (
                select(DbShift)
                .where(
                    DbShift.reference_id == reference_id,
                    DbShift.finished_at.is_(None),
                )
                .options(selectinload(DbShift.pauses))
                .order_by(*self.DEFAULT_SHIFT_ORDER_BY)
                .limit(1)
            )
            result = await session.execute(query)
            db_shift = result.scalar_one_or_none()
            return ShiftMapper.to_domain(db_shift) if db_shift else None

    async def get_open_started_at_or_before(
        self,
        cutoff: datetime,
    ) -> list[ShiftEntity]:
        async with Dependency.get(AsyncSession) as session:
            query = (
                select(DbShift)
                .where(
                    DbShift.finished_at.is_(None),
                    DbShift.started_at <= cutoff,
                )
                .options(selectinload(DbShift.pauses))
                .order_by(DbShift.started_at.asc(), DbShift.id.asc())
            )
            result = await session.scalars(query)
            return [ShiftMapper.to_domain(shift) for shift in result.all()]

    async def save(self, shift_entity: ShiftEntity) -> UUID:
        async with Dependency.get(AsyncSession) as session:
            if await self._has_overlap(session, shift_entity):
                raise OverlappingException(
                    ShiftEntity,
                    identifier=str(shift_entity.id),
                    start=shift_entity.started_at,
                    end=shift_entity.finished_at,
                )

            db_shift = await session.get(
                DbShift,
                shift_entity.id,
                options=(selectinload(DbShift.pauses),),
            )

            if db_shift is None:
                db_shift = ShiftMapper.from_domain(shift_entity)
                session.add(db_shift)
            else:
                ShiftMapper.update_model_from_domain(db_shift, shift_entity)

            await session.commit()
            return db_shift.id

    async def has_overlap(self, shift_entity: ShiftEntity) -> bool:
        async with Dependency.get(AsyncSession) as session:
            return await self._has_overlap(session, shift_entity)

    @staticmethod
    async def _has_overlap(
        session: AsyncSession,
        shift_entity: ShiftEntity,
    ) -> bool:
        filters = [
            DbShift.reference_id == shift_entity.reference_id,
            DbShift.id != shift_entity.id,
            or_(
                DbShift.finished_at.is_(None),
                DbShift.finished_at > shift_entity.started_at,
            ),
        ]

        if shift_entity.finished_at is not None:
            filters.append(DbShift.started_at < shift_entity.finished_at)

        query = select(exists().where(*filters))
        result = await session.execute(query)
        return result.scalar_one()

    async def get(self, id: UUID) -> ShiftEntity | None:
        async with Dependency.get(AsyncSession) as session:
            db_shift = await session.get(
                DbShift,
                id,
                options=(selectinload(DbShift.pauses),),
            )

            return ShiftMapper.to_domain(db_shift) if db_shift else None

    async def get_by_pause_id(self, pause_id: UUID) -> ShiftEntity | None:
        async with Dependency.get(AsyncSession) as session:
            query = (
                select(DbShift)
                .join(DbShift.pauses)
                .where(DbPause.id == pause_id)
                .options(selectinload(DbShift.pauses))
            )
            result = await session.execute(query)
            db_shift = result.scalar_one_or_none()
            return ShiftMapper.to_domain(db_shift) if db_shift else None

    async def remove(self, id: UUID) -> None:
        async with Dependency.get(AsyncSession) as session:
            db_shift = await session.get(
                DbShift,
                id,
                options=(selectinload(DbShift.pauses),),
            )

            if db_shift is None:
                return

            await session.delete(db_shift)
            await session.commit()
