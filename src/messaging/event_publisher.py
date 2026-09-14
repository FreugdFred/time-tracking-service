from nats.aio.client import Client as NatsClient

from src.core.settings import Settings
from src.core.unit_of_work import UnitOfWork
from src.messaging.command_repository import CommandMessagingRepository
from src.messaging.entity import EventEnvelope
from src.messaging.query_repository import QueryMessagingRepository


class EventPublisher:
    def __init__(
        self,
        command_repository: CommandMessagingRepository,
        query_repository: QueryMessagingRepository,
        settings: Settings,
        nats_client: NatsClient,
    ) -> None:
        if not nats_client.is_connected:
            raise RuntimeError("NATS client is not connected")

        self.command_repository = command_repository
        self.query_repository = query_repository
        self.settings = settings
        self.nats_client = nats_client

    async def publish(self) -> None:
        events = await self.query_repository.list_unpublished()

        for event in events:
            await self._publish_event(event)

    async def _publish_event(self, event: EventEnvelope):
        async with UnitOfWork() as session:
            await self.command_repository.set_publish(session, event.id)
            await self.nats_client.publish(
                subject=f"{self.settings.PROJECT_NAME}.{event.type}",
                payload=event.model_dump_json().encode("utf-8"),
            )
