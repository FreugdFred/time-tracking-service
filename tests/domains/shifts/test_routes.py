from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domains.shifts.routes import shift_router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(shift_router)
    return TestClient(app)


def test_clock_route_returns_shift_id(client: TestClient) -> None:
    response = client.post("/shift/clock", params={"reference_id": "employee-1"})

    assert response.status_code == 200, response.text
    assert UUID(response.json())


def test_reference_route_translates_filters_and_pagination(
    client: TestClient,
) -> None:
    response = client.get(
        "/shift/reference/employee-1",
        params={
            "approved": "false",
            "automatically_closed": "true",
            "is_open": "false",
            "sort_direction": "asc",
            "limit": 20,
            "offset": 5,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 5,
    }
