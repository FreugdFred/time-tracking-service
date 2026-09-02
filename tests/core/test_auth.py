from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from dependency_container import Dependency
from src.core.auth import verify_api_key
from src.core.settings import Settings


def create_client(api_key: str) -> TestClient:
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
            "API_KEY": api_key,
        }
    )
    Dependency.register_instance(Settings, settings)

    app = FastAPI(dependencies=[Depends(verify_api_key)])

    @app.get("/protected")
    async def protected_route() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


def test_missing_api_key_is_unauthorized() -> None:
    response = create_client("secret").get("/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_invalid_api_key_is_unauthorized() -> None:
    response = create_client("secret").get(
        "/protected",
        headers={"X-API-Key": "incorrect"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}


def test_valid_api_key_allows_request() -> None:
    response = create_client("secret").get(
        "/protected",
        headers={"X-API-Key": "secret"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
