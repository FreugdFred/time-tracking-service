from pydantic import BaseModel

from src.core.schema_types import ReferenceId


class ClockShiftCommand(BaseModel):
    reference_id: ReferenceId
