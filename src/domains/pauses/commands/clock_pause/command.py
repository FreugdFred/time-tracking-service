from pydantic import BaseModel

from src.core.schema_types import ReferenceId


class ClockPauseCommand(BaseModel):
    reference_id: ReferenceId
