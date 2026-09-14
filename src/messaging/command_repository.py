from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.messaging.entity import BaseDomainEvent
from src.messaging.mapper import MessagingMapper
from src.messaging.models import DbEvent


class CommandMessagingRepository:
    async def remove_published_at_or_before(
        self,
        session: AsyncSession,
        cutoff: datetime,
    ) -> None:
        query = delete(DbEvent).where(
            DbEvent.published_at.is_not(None),
            DbEvent.published_at <= cutoff,
        )
        await session.execute(query)

    async def set_publish(self, session: AsyncSession, id: UUID) -> None:
        query = (
            update(DbEvent)
            .where(DbEvent.id == id)
            .values(published_at=func.now())
        )

        await session.execute(query)

    async def save_many(
        self,
        session: AsyncSession,
        events: Iterable[BaseDomainEvent],
    ) -> None:
        db_events = [MessagingMapper.from_domain(event) for event in events]
        session.add_all(db_events)
