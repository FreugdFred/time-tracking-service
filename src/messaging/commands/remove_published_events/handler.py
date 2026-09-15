from datetime import timedelta

from time_provider import AbstractTimeProvider

from src.core.handler_base import HandlerBase
from src.core.unit_of_work import UnitOfWork
from messaging.commands.repository import CommandMessagingRepository
from src.messaging.commands.remove_published_events.command import (
    RemovePublishedEventsCommand,
)


class RemovePublishedEventsCommandHandler(HandlerBase):
    def __init__(
        self,
        messaging_repository: CommandMessagingRepository,
        time_provider: AbstractTimeProvider,
    ) -> None:
        self._messaging_repository = messaging_repository
        self._time_provider = time_provider

    async def handle(self, command: RemovePublishedEventsCommand) -> None:
        cutoff = self._time_provider.now() - timedelta(minutes=command.retention_minutes)

        async with UnitOfWork() as session:
            await self._messaging_repository.remove_published_at_or_before(
                session,
                cutoff,
            )
