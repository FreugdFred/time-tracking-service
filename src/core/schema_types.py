from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator

from dependency_container import Dependency
from time_provider import AbstractTimeProvider


def normalize_to_utc(value: datetime) -> datetime:
    return Dependency.get(AbstractTimeProvider).normalize_to_utc(value)


UtcDateTimeInput = Annotated[datetime, AfterValidator(normalize_to_utc)]
