from collections.abc import Iterable

from dependency_container import Dependency
from nats.aio.client import Client as NatsClient

from src.core.events import DomainEvent
from src.core.settings import Settings


class HandlerBase:
    @staticmethod
    async def publish_events(events: Iterable[DomainEvent]) -> None:
        for event in events:
            await HandlerBase.publish_event(event)

    @staticmethod
    async def publish_event(event: DomainEvent) -> None:
        settings = Dependency.get(Settings)

        if not settings.NATS_URL:
            return None

        nats_client = HandlerBase.get_nats_client()
        await nats_client.publish(
            subject=f"{settings.PROJECT_NAME}.{type(event).__name__}",
            payload=event.model_dump_json().encode("utf-8"),
        )

    @staticmethod
    def get_nats_client() -> NatsClient:
        nats_client = Dependency.get(NatsClient)

        if not nats_client.is_connected:
            raise RuntimeError("NATS client is not connected")

        return nats_client
