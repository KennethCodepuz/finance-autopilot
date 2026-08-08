"""
Phase 6 Tests — Audit Logs REST API & Real-Time Activity WebSocket

Tests cover:
1. GET /api/audit/logs pagination (limit, offset)
2. GET /api/audit/logs filtering (actor_type, action)
3. GET /api/audit/logs dynamic is_verified status (valid vs tampered logs)
4. WS /api/ws/activity WebSocket connection and message streaming

Run with: uv --directory backend run pytest tests/test_phase6.py -v
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.audit import AuditLog
from app.services.audit_service import create_and_verify_audit_log
from app.core.database import get_db
from app.core.redis import get_redis_ws

# ---------------------------------------------------------------------------
# Test Data Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture
def client(db_session: AsyncSession):
    """
    FastAPI TestClient with overridden get_db dependency pointing
    to the in-memory test database session and mocked Redis pool.
    """
    async def _get_db_override():
        yield db_session

    mock_redis_pool = AsyncMock()
    mock_redis_pool.close = AsyncMock()

    app.dependency_overrides[get_db] = _get_db_override
    with patch("app.main.create_pool", return_value=mock_redis_pool):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Audit Logs REST API Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_audit_logs_empty(client: TestClient):
    """Test GET /api/audit/logs returns an empty list when no audit logs exist."""
    response = client.get("/api/audit/logs")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_audit_logs_pagination_and_verified(client: TestClient, db_session: AsyncSession):
    """
    Test GET /api/audit/logs returns correctly ordered logs with dynamic is_verified=True.
    """
    # Create 3 valid audit log entries in sequence
    log1 = await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"action_type": "transfer", "amount": 100.0},
        target_id=1,
        target_type="ledger",
        actor_id="agent_1",
        action="proposal.created",
        actor_type="agent"
    )
    log2 = await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"action_type": "approve", "amount": 100.0},
        target_id=1,
        target_type="ledger",
        actor_id="human_1",
        action="proposal_approved",
        actor_type="human"
    )
    log3 = await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"action_type": "confirm", "amount": 100.0},
        target_id=1,
        target_type="ledger",
        actor_id="system_1",
        action="ledger_entry.confirmed",
        actor_type="system"
    )

    # Test default query (newest sequence first)
    res = client.get("/api/audit/logs")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    assert data[0]["sequence_number"] == 3
    assert data[0]["is_verified"] is True
    assert data[1]["sequence_number"] == 2
    assert data[1]["is_verified"] is True
    assert data[2]["sequence_number"] == 1
    assert data[2]["is_verified"] is True

    # Test limit and offset pagination
    res_paginated = client.get("/api/audit/logs?limit=2&offset=1")
    print(res_paginated)
    assert res_paginated.status_code == 200
    data_paginated = res_paginated.json()
    assert len(data_paginated) == 2
    assert data_paginated[0]["sequence_number"] == 2
    assert data_paginated[1]["sequence_number"] == 1


@pytest.mark.asyncio
async def test_get_audit_logs_filtering(client: TestClient, db_session: AsyncSession):
    """Test GET /api/audit/logs filtering by actor_type and action."""
    await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"test": "agent_action"},
        target_id=1,
        target_type="ledger",
        actor_id="agent_alpha",
        action="proposal.created",
        actor_type="agent"
    )
    await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"test": "human_action"},
        target_id=2,
        target_type="ledger",
        actor_id="human_operator",
        action="proposal_approved",
        actor_type="human"
    )

    # Filter by actor_type=agent
    res_agent = client.get("/api/audit/logs?actor_type=agent")
    assert res_agent.status_code == 200
    data_agent = res_agent.json()
    assert len(data_agent) == 1
    assert data_agent[0]["actor_type"] == "agent"
    assert data_agent[0]["actor_id"] == "agent_alpha"

    # Filter by action=proposal_approved
    res_action = client.get("/api/audit/logs?action=proposal_approved")
    assert res_action.status_code == 200
    data_action = res_action.json()
    assert len(data_action) == 1
    assert data_action[0]["action"] == "proposal_approved"
    assert data_action[0]["actor_type"] == "human"


@pytest.mark.asyncio
async def test_get_audit_logs_detects_tampered_log(client: TestClient, db_session: AsyncSession):
    """
    Test GET /api/audit/logs dynamically returns is_verified=False when a log's hash or payload is tampered with.
    """
    log = await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"amount": 500.0},
        target_id=1,
        target_type="ledger",
        actor_id="agent_1",
        action="proposal.created",
        actor_type="agent"
    )

    # Tamper with the row directly in memory/database
    log.current_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    await db_session.commit()

    res = client.get("/api/audit/logs")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["is_verified"] is False
    assert data[0]["current_hash"] == "0000000000000000000000000000000000000000000000000000000000000000"


# ---------------------------------------------------------------------------
# 2. Activity Feed WebSocket Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_websocket_activity_feed_stream(client: TestClient):
    """
    Test WS /api/ws/activity receives streamed messages published to the Redis 'activity_feed' channel.
    """
    mock_event = {
        "event_type": "proposal.created",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "ledger_id": 1,
            "action_type": "transfer",
            "amount": 1500.0,
            "payee": "Mock Supplier",
            "risk_score": 25,
            "risk_tier": "medium",
            "status": "pending_approval"
        }
    }

    # Mock Redis pubsub object for TestClient websocket execution
    class AsyncPubSubMock:
        async def subscribe(self, channel):
            pass
        async def unsubscribe(self, channel):
            pass
        async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
            return {
                "type": "message",
                "data": json.dumps(mock_event).encode("utf-8")
            }

    class AsyncRedisMock:
        def pubsub(self):
            return AsyncPubSubMock()
        async def close(self):
            pass

    async def _get_redis_ws_override():
        return AsyncRedisMock()

    app.dependency_overrides[get_redis_ws] = _get_redis_ws_override
    try:
        with patch("redis.asyncio.Redis.from_url", return_value=AsyncRedisMock()):
            with client.websocket_connect("/api/ws/activity") as websocket:
                data = websocket.receive_json()
                assert data["event_type"] == "proposal.created"
                assert data["payload"]["ledger_id"] == 1
                assert data["payload"]["amount"] == 1500.0
                assert data["payload"]["payee"] == "Mock Supplier"
    finally:
        app.dependency_overrides.pop(get_redis_ws, None)
