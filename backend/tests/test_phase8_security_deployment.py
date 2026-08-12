from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.main import app


@pytest.fixture
def client(db_session: AsyncSession):
    async def _get_db_override():
        yield db_session

    mock_redis_pool = AsyncMock()
    mock_redis_pool.close = AsyncMock()

    app.dependency_overrides[get_db] = _get_db_override
    with patch("app.main.create_pool", return_value=mock_redis_pool):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


def test_health_check_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "env" in data


def test_cors_headers_handling(client: TestClient):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_settings_configuration_integrity():
    assert settings.app_env in ["development", "production", "testing"]
    assert settings.algorithm == "HS256"
    assert settings.redis_url.startswith("redis")
