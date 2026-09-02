import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from dependency_container import Dependency
from src.core.settings import Settings

api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(user_key: str = Depends(api_key_header)) -> str:
    settings_api_key = Dependency.get(Settings).API_KEY
    if settings_api_key is None or not secrets.compare_digest(
        user_key,
        settings_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return user_key
