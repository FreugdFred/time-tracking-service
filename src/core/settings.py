from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, NatsDsn, PositiveInt


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Time-Tracking-Service-API"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    SHIFT_AUTO_CLOSE_AFTER_HOURS: PositiveInt = 12
    API_KEY: str | None = None

    DATABASE_URL: AnyUrl
    NATS_URL: NatsDsn | None = None

    # operational
    LOCAL_TIMEZONE: str = "Europe/Amsterdam"

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )
