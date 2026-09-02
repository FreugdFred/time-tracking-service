from uuid import UUID

from pydantic import BaseModel


class RemoveShiftCommand(BaseModel):
    id: UUID