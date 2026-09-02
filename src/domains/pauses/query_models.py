from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PauseQueryModel(BaseModel):
    id: UUID
    shift_id: UUID
    started_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
