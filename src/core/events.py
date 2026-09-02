from datetime import datetime

from pydantic import BaseModel, Field

from src.utils import get_now


class DomainEvent(BaseModel):
    reference_id: str
    occurrence_datetime: datetime = Field(default_factory=get_now)