from dependency_container import Dependency

from src.core.settings import Settings
from src.messaging.event_publisher import EventPublisher


async def publish_events() -> None:
    if Dependency.get(Settings).NATS_URL is None:
        return

    event_publisher = Dependency.get(EventPublisher)
    await event_publisher.publish()
