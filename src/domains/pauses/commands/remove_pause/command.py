from uuid import UUID

from pydantic import BaseModel


class RemovePauseCommand(BaseModel):
    id: UUID
