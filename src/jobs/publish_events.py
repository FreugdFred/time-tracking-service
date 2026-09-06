from dependency_container import Dependency
from messaging.event_publisher import EventPublisher


async def publish_events() -> None:
    event_publisher = Dependency.get(EventPublisher)
    await event_publisher.publish()