from pydantic import BaseModel


class ClockPauseCommand(BaseModel):
    reference_id: str
