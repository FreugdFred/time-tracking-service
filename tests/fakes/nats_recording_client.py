from nats.aio.client import Client as NatsClient


class RecordingNatsClient(NatsClient):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[tuple[str, bytes]] = []

    async def publish(
        self,
        subject: str,
        payload: bytes = b"",
        reply: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.messages.append((subject, payload))
