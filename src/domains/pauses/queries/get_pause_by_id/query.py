from uuid import UUID

from pydantic import BaseModel


class GetPauseByIdQuery(BaseModel):
    id: UUID
