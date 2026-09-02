import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base
from src.core.mixins import TimestampMixin
from src.core.types import TimezoneAwareDateTime

if TYPE_CHECKING:
    from src.domains.pauses.models import DbPause


class DbShift(Base, TimestampMixin):
    __tablename__ = "shift"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    reference_id: Mapped[str] = mapped_column()

    started_at: Mapped[datetime] = mapped_column(
        TimezoneAwareDateTime(), nullable=False
    )
    finished_at: Mapped[datetime] = mapped_column(
        TimezoneAwareDateTime(), nullable=True
    )

    automatically_closed: Mapped[bool] = mapped_column(nullable=False, default=False)

    approved: Mapped[bool] = mapped_column(nullable=False, default=False)

    pauses: Mapped[list["DbPause"]] = relationship(
        back_populates="shift", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "(finished_at IS NULL) OR (started_at < finished_at)",
            name="check_started_before_finished",
        ),
    )
