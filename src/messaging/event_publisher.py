from nats.aio.client import Client as NatsClient

from messaging.repository import MessagingRepository
from src.core.settings import Settings

class EventPublisher:
    def __init__(self, repository: MessagingRepository, settings: Settings, nats_client: NatsClient):
        if not nats_client.is_connected:
            raise RuntimeError("NATS client is not connected")

        self.repository = repository
        self.settings = settings
        self.nats_client = nats_client


    async def publish(self):
        events = await self.repository.list_unpublished()

        for event in events:
            await self.nats_client.publish(
                subject=f"{self.settings.PROJECT_NAME}.{type(event).__name__}",
                payload=event.model_dump_json().encode("utf-8"),
            )
            await self.repository.set_publish(event.id)

