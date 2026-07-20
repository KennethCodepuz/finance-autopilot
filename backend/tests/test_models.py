from datetime import date, datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.account import Account
from app.models.audit import AuditLog
from app.models.idempotency import IdempotencyKey
from app.models.ledger import OutboxLedger
from app.models.transaction import Transaction


from sqlalchemy.orm import selectinload


@pytest.mark.asyncio
async def test_create_account_and_transaction(db_session):
    # Create account
    acc = Account(
        plaid_account_id="acc_12345",
        item_id="item_999",
        name="Plaid Checking",
        official_name="Plaid Gold Checking",
        type="depository",
        subtype="checking",
        mask="0000",
        balance_available=1000.50,
        balance_current=1200.00,
        iso_currency_code="USD",
    )
    db_session.add(acc)
    await db_session.commit()
    await db_session.refresh(acc)

    assert acc.id is not None
    assert acc.plaid_account_id == "acc_12345"

    # Create transaction tied to account
    txn = Transaction(
        account_id=acc.id,
        plaid_transaction_id="txn_abc123",
        amount=45.99,
        date=date(2026, 7, 20),
        name="Coffee Shop",
        merchant_name="Starbucks",
        category="Food and Drink",
        pending=False,
    )
    db_session.add(txn)
    await db_session.commit()
    await db_session.refresh(txn)

    assert txn.id is not None
    assert txn.account_id == acc.id

    # Verify relationship query with selectinload
    result = await db_session.execute(
        select(Account).options(selectinload(Account.transactions)).where(Account.id == acc.id)
    )
    fetched_acc = result.scalar_one()
    assert len(fetched_acc.transactions) == 1
    assert fetched_acc.transactions[0].name == "Coffee Shop"


@pytest.mark.asyncio
async def test_duplicate_plaid_account_id_raises_integrity_error(db_session):
    acc1 = Account(
        plaid_account_id="acc_duplicate",
        item_id="item_1",
        name="Account 1",
        type="depository",
    )
    acc2 = Account(
        plaid_account_id="acc_duplicate",
        item_id="item_2",
        name="Account 2",
        type="depository",
    )
    db_session.add(acc1)
    await db_session.commit()

    db_session.add(acc2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_idempotency_key_and_outbox_ledger(db_session):
    ikey = IdempotencyKey(
        key="uuid-1234-5678-90ab",
        endpoint="/api/v1/tools/categorize",
        request_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status="processing",
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(ikey)
    await db_session.commit()
    await db_session.refresh(ikey)

    ledger = OutboxLedger(
        idempotency_key_id=ikey.id,
        idempotency_key=ikey.key,
        action_type="categorize_transaction",
        payload={"transaction_id": "txn_123", "category": "Utilities"},
        status="pending",
        risk_score=5,
        risk_tier="low",
    )
    db_session.add(ledger)
    await db_session.commit()
    await db_session.refresh(ledger)

    assert ledger.id is not None
    assert ledger.idempotency_key_id == ikey.id
    assert ledger.risk_tier == "low"


@pytest.mark.asyncio
async def test_audit_log_creation(db_session):
    audit = AuditLog(
        sequence_number=1,
        actor_type="agent",
        actor_id="finance_agent_v1",
        action="categorize_transaction",
        target_type="transaction",
        target_id="txn_123",
        payload={"new_category": "Subscriptions"},
        prev_hash="0" * 64,
        current_hash="a" * 64,
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.id is not None
    assert audit.sequence_number == 1
    assert audit.actor_type == "agent"
