from datetime import datetime

from dependency_container import Dependency
from time_provider import AbstractTimeProvider


def get_now() -> datetime:
    return Dependency.get(AbstractTimeProvider).now()
