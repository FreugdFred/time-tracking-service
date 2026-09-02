import sys

from fastapi import Depends, FastAPI
from loguru import logger

import src.dependencies  # noqa: F401
from dependency_container import Dependency
from src.core.auth import verify_api_key
from src.core.settings import Settings
from src.domains.pauses.routes import pause_router
from src.domains.shifts.routes import shift_router
from src.exception_handlers import register_exception_handlers
from src.lifespan import lifespan

settings = Dependency.get(Settings)

logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL)
logger.add(
    "logs/app.log",
    level=settings.LOG_LEVEL,
    rotation="00:00",
    retention="7 days",
)

app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)

dependencies = []

if settings.API_KEY:
    dependencies.append(Depends(verify_api_key))

app.include_router(shift_router, dependencies=dependencies)
app.include_router(pause_router, dependencies=dependencies)

register_exception_handlers(app)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
