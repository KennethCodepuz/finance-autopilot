from unittest.mock import AsyncMock
import pytest
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.ledger import OutboxLedger
from app.models.idempotency import IdempotencyKey
from app.models.audit import AuditLog
from app.services.risk_service import calculate_risk_score
from app.services.agent_service import propose_action
from app.workers.task import execute_ledger_entry

@pytest.mark.asyncio
async def test_calculate_risk_score_low(db_session: AsyncSession):
    # Standard low risk action (score = 8 because payee is new)
    result = await calculate_risk_score("payment", 100.0, "Uber", db_session)
    assert result["score"] == 8
    assert result["tier"] == "low"
    assert "Payee is new: +8" in result["factors"]

@pytest.mark.asyncio
async def test_calculate_risk_score_high(db_session: AsyncSession):
    # High risk action: amount=600 (>500: +7), transfer (+5), new payee (+8) -> 20 -> high
    result = await calculate_risk_score("transfer", 600.0, "NewPayee", db_session)
    assert result["score"] == 20
    assert result["tier"] == "high"

@pytest.mark.asyncio
async def test_propose_action_low_risk(db_session: AsyncSession):
    mock_redis = AsyncMock()
    
    # 1. Propose low risk action
    ledger_entry = await propose_action(
        action_type="payment",
        amount=50.0,
        payee="SomePayee",
        account_id=1,
        session=db_session,
        redis=mock_redis
    )
    
    assert ledger_entry.id is not None
    assert ledger_entry.status == "pending"
    assert ledger_entry.risk_tier == "low"
    
    # Verify Redis enqueue was called
    mock_redis.enqueue_job.assert_called_once_with("execute_ledger_entry", ledger_entry.id)
    
    # Verify Audit log was created
    audit = await db_session.execute(select(AuditLog).where(AuditLog.target_id == str(ledger_entry.id)))
    audit_entry = audit.scalars().first()
    assert audit_entry is not None
    assert audit_entry.action == "proposal.created"

@pytest.mark.asyncio
async def test_propose_action_high_risk(db_session: AsyncSession):
    mock_redis = AsyncMock()
    
    # 2. Propose high risk action
    ledger_entry = await propose_action(
        action_type="transfer",
        amount=2500.0,
        payee="SuspiciousPayee",
        account_id=1,
        session=db_session,
        redis=mock_redis
    )
    
    assert ledger_entry.status == "pending"
    assert ledger_entry.risk_tier == "high"
    
    # Verify Redis enqueue was NOT called for high risk
    mock_redis.enqueue_job.assert_not_called()

@pytest.mark.asyncio
async def test_execute_ledger_entry_task(db_session: AsyncSession):
    # Create OutboxLedger and IdempotencyKey manually to execute the task on them
    idempotency_key = IdempotencyKey(
        key="test-key-123",
        endpoint="execute_ledger_entry",
        request_hash="somehash",
        status="processing",
        expires_at=pytest.importorskip("datetime").datetime.now()
    )
    db_session.add(idempotency_key)
    await db_session.flush()
    
    ledger_entry = OutboxLedger(
        action_type="transfer",
        idempotency_key=idempotency_key.key,
        idempotency_key_id=idempotency_key.id,
        payload={"amount": 100.0, "payee": "TestPayee"},
        status="pending",
        risk_score=5,
        risk_tier="low"
    )
    db_session.add(ledger_entry)
    await db_session.commit()
    
    ctx = {"session": db_session}
    await execute_ledger_entry(ctx, ledger_entry.id)
    
    # Verify DB changes
    await db_session.refresh(ledger_entry)
    await db_session.refresh(idempotency_key)
    assert ledger_entry.status == "confirmed"
    assert idempotency_key.status == "completed"

# FastAPI Endpoints Integration Tests
@pytest.mark.asyncio
async def test_approval_routes(db_session: AsyncSession):
    mock_redis = AsyncMock()
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: mock_redis
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Propose low-risk action (auto-executes)
        response = await client.post(
            "/api/approvals/propose",
            json={
                "action_type": "payment",
                "amount": 10.0,
                "payee": "GasStation",
                "account_id": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "low"
        assert data["status"] == "pending"
        
        # 2. Propose high-risk action (awaits approval)
        response = await client.post(
            "/api/approvals/propose",
            json={
                "action_type": "transfer",
                "amount": 5000.0,
                "payee": "UnknownPayee",
                "account_id": 2
            }
        )
        assert response.status_code == 200
        high_risk_data = response.json()
        print("RESPONSE BODY:", response.text)
        assert high_risk_data["tier"] == "high"
        
        # 3. Get pending approvals
        response = await client.get("/api/approvals/pending-approvals")
        assert response.status_code == 200
        approvals = response.json()
        assert len(approvals) >= 1
        assert any(item["id"] == high_risk_data["ledger_id"] for item in approvals)
        
        # 4. Approve the pending action
        ledger_id = high_risk_data["ledger_id"]
        response = await client.post(f"/api/approvals/approve/{ledger_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Action approved successfully"
        
        # 5. Propose another high-risk action to reject
        response = await client.post(
            "/api/approvals/propose",
            json={
                "action_type": "transfer",
                "amount": 9000.0,
                "payee": "FraudPayee",
                "account_id": 2
            }
        )
        reject_id = response.json()["ledger_id"]
        
        # 6. Reject it
        response = await client.post(f"/api/approvals/reject/{reject_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Action rejected successfully"
        
        # Verify status changed to rejected in DB
        res = await db_session.execute(select(OutboxLedger).where(OutboxLedger.id == reject_id))
        rejected_entry = res.scalars().first()
        assert rejected_entry.status == "rejected"
        
    # Clean up overrides
    app.dependency_overrides.clear()
