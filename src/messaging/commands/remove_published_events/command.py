from pydantic import BaseModel, PositiveInt


class RemovePublishedEventsCommand(BaseModel):
    retention_minutes: PositiveInt
