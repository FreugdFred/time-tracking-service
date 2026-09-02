from pydantic import BaseModel, PositiveInt


class CloseOpenShiftsCommand(BaseModel):
    close_after_hours: PositiveInt