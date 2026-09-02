from pydantic import BaseModel


class ClockShiftCommand(BaseModel):
    reference_id: str
