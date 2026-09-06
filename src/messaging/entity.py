import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from utils import get_now


class BaseDomainEvent(BaseModel):
    reference_id: str
    occurrence_datetime: datetime = Field(default_factory=get_now)


class EventEnvelope(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: str
    subject: str
    data: dict[str, Any]
