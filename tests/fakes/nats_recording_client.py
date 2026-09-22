from nats.aio.client import Client as NatsClient


class RecordingNatsClient(NatsClient):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[tuple[str, bytes]] = []
        self.flush_error: Exception | None = None
        self.confirmed_messages: list[tuple[str, bytes]] = []

    async def publish(
        self,
        subject: str,
        payload: bytes = b"",
        reply: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.messages.append((subject, payload))

    async def flush(self, timeout: int = 10) -> None:
        if self.flush_error is not None:
            raise self.flush_error

        self.confirmed_messages = self.messages.copy()
