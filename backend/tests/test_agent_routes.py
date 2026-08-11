from datetime import date
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.main import app
from app.models.account import Account
from app.models.transaction import Transaction


@pytest.fixture
def client(db_session: AsyncSession):
    """FastAPI TestClient fixture with overridden DB and Redis dependencies."""
    async def _get_db_override():
        yield db_session

    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_redis.enqueue_job = AsyncMock()

    async def _get_redis_override():
        return mock_redis

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_redis] = _get_redis_override

    mock_redis_pool = AsyncMock()
    mock_redis_pool.close = AsyncMock()

    with patch("app.main.create_pool", return_value=mock_redis_pool):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()


def test_get_agent_tools_endpoint(client: TestClient):
    response = client.get("/api/agent/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) == 3
    tool_names = [t["function"]["name"] for t in data["tools"]]
    assert "categorize_transaction" in tool_names
    assert "transfer_funds" in tool_names
    assert "flag_anomaly" in tool_names


def test_post_agent_prompt_transfer(client: TestClient):
    payload = {"prompt": "Please transfer $150 to Savings Account"}
    response = client.post("/api/agent/prompt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prompt"] == "Please transfer $150 to Savings Account"
    assert "tools_called" in data
    assert len(data["tools_called"]) >= 1
    tc = data["tools_called"][0]
    assert tc["tool_name"] == "transfer_funds"
    assert tc["status"] == "proposed"


@pytest.mark.asyncio
async def test_post_agent_prompt_categorize(client: TestClient, db_session: AsyncSession):
    # Setup test account and transaction
    acc = Account(
        plaid_account_id="acc_789",
        item_id="item_789",
        name="Checking",
        type="depository",
        balance_current=2000.0,
    )
    db_session.add(acc)
    await db_session.flush()

    tx = Transaction(
        account_id=acc.id,
        plaid_transaction_id="tx_789",
        amount=25.0,
        date=date(2026, 8, 11),
        name="Supermarket",
        category="Uncategorized",
    )
    db_session.add(tx)
    await db_session.commit()

    payload = {"prompt": "Categorize transaction #1 as Groceries"}
    response = client.post("/api/agent/prompt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools_called"]) >= 1
    tc = data["tools_called"][0]
    assert tc["tool_name"] == "categorize_transaction"
    assert tc["status"] == "executed"


def test_post_agent_prompt_empty_validation_error(client: TestClient):
    payload = {"prompt": ""}
    response = client.post("/api/agent/prompt", json=payload)
    assert response.status_code == 422  # Validation error for empty string


def test_post_agent_prompt_general_query(client: TestClient):
    payload = {"prompt": "What is the weather today?"}
    response = client.post("/api/agent/prompt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools_called"]) == 0
    assert "No actionable financial operation" in data["agent_thought"]
