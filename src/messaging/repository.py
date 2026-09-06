from uuid import UUID

from dependency_container import Dependency
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from messaging.entity import BaseDomainEvent, EventEnvelope
from messaging.mapper import MessagingMapper
from messaging.models import DbEvent


class MessagingRepository:
    async def list_unpublished(self, amount: int = 100) -> list[EventEnvelope]:
        query = (
            select(DbEvent)
            .where(DbEvent.published_at.is_(None))
            .order_by(DbEvent.occurred_at.asc(), DbEvent.id.asc())
            .limit(amount)
        )

        async with Dependency.get(AsyncSession) as session:
            result = await session.scalars(query)
            return [MessagingMapper.to_domain(event) for event in result.all()]

    async def set_publish(self, id: UUID) -> None:
        query = (
            update(DbEvent)
            .where(DbEvent.id == id)
            .values(published_at=func.now())
        )

        async with Dependency.get(AsyncSession) as session:
            await session.execute(query)
            await session.commit()

    async def save(self, event: BaseDomainEvent) -> None:
        db_event = MessagingMapper.from_domain(event)  # pyright: ignore[reportArgumentType]

        async with Dependency.get(AsyncSession) as session:
            session.add(db_event)
            await session.commit()
