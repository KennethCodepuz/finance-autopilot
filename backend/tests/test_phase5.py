"""
Phase 5 Tests — Tamper-Evident Audit Trail System

Tests cover:
1. recompute_hash()           — pure hash recomputation from stored fields
2. create_and_verify_audit_log() — creates a new audit log and verifies the chain
3. verify_audit_chain_incremental — ARQ job that verifies new rows since checkpoint
4. verify_audit_chain_full       — ARQ job that verifies the entire chain from Row 1

Run with: uv --directory backend run pytest tests/test_phase5.py -v
"""

import hashlib
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.services.audit_service import (
    recompute_hash,
    create_and_verify_audit_log,
)
from app.workers.task import (
    verify_audit_chain_incremental,
    verify_audit_chain_full,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_audit_log(
    sequence_number: int,
    actor_type: str = "agent",
    actor_id: str = "agent_default",
    action: str = "action_proposed",
    target_type: str = "ledger",
    target_id: str = "1",
    audit_payload: dict | None = None,
    prev_hash: str = "0",
    timestamp: datetime | None = None,
) -> AuditLog:
    """
    Build an AuditLog object with a correctly computed current_hash.
    Mirrors exactly what calculate_audit_hash does, so tests start from
    a known-good baseline.
    """
    if audit_payload is None:
        audit_payload = { "action_type": "propose", "amount": 100.0, "payee": "TestPayee", "account_id": 1}
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    hash_payload = {
        "sequence_number": sequence_number,
        "timestamp": timestamp.isoformat(),
        "prev_hash": prev_hash,
        "actor_id": actor_id,
        "actor_type": actor_type,
        "action": action,
        "target_type": target_type,
        "target_id": str(target_id),
        "payload": audit_payload,
    }

    current_hash = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True).encode()
    ).hexdigest()

    log = AuditLog(
        sequence_number=sequence_number,
        timestamp=timestamp,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        payload=hash_payload,
        prev_hash=prev_hash,
        current_hash=current_hash,
    )
    return log


# ---------------------------------------------------------------------------
# 1. recompute_hash() tests
# ---------------------------------------------------------------------------

def test_recompute_hash_matches_stored_hash():
    """
    A freshly built audit log's recomputed hash must match its stored current_hash.
    This is the baseline: if recompute_hash() is correct, this will always pass.
    """
    log = _make_audit_log(sequence_number=1)
    recomputed = recompute_hash(log)
    assert recomputed == log.current_hash


def test_recompute_hash_detects_payload_tampering():
    """
    If someone edits the payload dict in the database, recompute_hash()
    must return a DIFFERENT hash from the stored current_hash.
    """
    log = _make_audit_log(sequence_number=1)
    original_hash = log.current_hash

    # Simulate a direct database edit of the payload
    log.payload["payload"]["amount"] = 99999.0

    recomputed = recompute_hash(log)
    assert recomputed != original_hash


def test_recompute_hash_detects_action_tampering():
    """
    Changing the 'action' field must produce a different recomputed hash.
    """
    log = _make_audit_log(sequence_number=1, action="action_proposed")
    log.action = "action_approved"  # silently changed in DB

    recomputed = recompute_hash(log)
    assert recomputed != log.current_hash


def test_recompute_hash_detects_actor_tampering():
    """
    Changing actor_id must produce a different recomputed hash.
    """
    log = _make_audit_log(sequence_number=1, actor_id="agent_default")
    log.actor_id = "attacker"  # silently changed in DB

    recomputed = recompute_hash(log)
    assert recomputed != log.current_hash


# ---------------------------------------------------------------------------
# 2. create_and_verify_audit_log() tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_verify_creates_valid_chain(db_session: AsyncSession):
    """
    create_and_verify_audit_log should create a new AuditLog whose
    prev_hash points to the previous entry's current_hash, and whose
    current_hash is correctly computed.
    """
    # Create and save Row 1 (genesis)
    row1 = await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"amount": 100.0, "payee": "Alice"},
        target_id=1,
        target_type="ledger",
        actor_id="agent_default",
        action="action_proposed",
        actor_type="agent",
    )
    db_session.add(row1)
    await db_session.flush()

    # Create Row 2, linked to Row 1
    row2 = await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"amount": 200.0, "payee": "Bob"},
        target_id=2,
        target_type="ledger",
        actor_id="human_default",
        action="action_approved",
        actor_type="human",
    )
    db_session.add(row2)
    await db_session.flush()

    # Row 1: genesis entry should have prev_hash = "0"
    assert row1.prev_hash == "0"
    assert recompute_hash(row1) == row1.current_hash

    # Row 2: must link to Row 1
    assert row2.prev_hash == row1.current_hash
    assert recompute_hash(row2) == row2.current_hash


@pytest.mark.asyncio
async def test_create_and_verify_raises_on_broken_chain(db_session: AsyncSession):
    """
    If the last stored audit log in the database has been tampered with
    (its current_hash no longer matches its fields), create_and_verify_audit_log
    must raise an exception and refuse to write a new log linked to corrupted data.
    """
    # Write a valid Row 1
    row1 = await create_and_verify_audit_log(
        session=db_session,
        audit_payload={"amount": 100.0, "payee": "Alice"},
        target_id=1,
        target_type="ledger",
        actor_id="agent_default",
        action="action_proposed",
        actor_type="agent",
    )
    db_session.add(row1)
    await db_session.flush()

    # Tamper with Row 1 by mutating its payload but keeping current_hash unchanged
    row1.payload = {"amount": 99999.0, "payee": "Attacker"}
    await db_session.flush()

    # Attempting to create Row 2 must raise because Row 1 is corrupt
    with pytest.raises(Exception):
        await create_and_verify_audit_log(
            session=db_session,
            audit_payload={"amount": 200.0, "payee": "Bob"},
            target_id=2,
            target_type="ledger",
            actor_id="agent_default",
            action="action_proposed",
            actor_type="agent",
        )


# ---------------------------------------------------------------------------
# 3. verify_audit_chain_incremental job tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_incremental_verify_passes_clean_chain(db_session: AsyncSession):
    """
    Incremental verification should pass without raising for a clean chain.
    The checkpoint in Redis should be updated to the latest sequence number.
    """
    # Build a 3-entry chain directly in the DB
    prev_hash = "0"
    for i in range(1, 4):
        log = _make_audit_log(sequence_number=i, prev_hash=prev_hash)
        db_session.add(log)
        await db_session.flush()
        prev_hash = log.current_hash
    await db_session.commit()

    mock_redis = AsyncMock()
    # Simulate checkpoint: start from 0 (no previous checkpoint)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()

    ctx = {"session": db_session, "redis": mock_redis}
    # Should not raise
    await verify_audit_chain_incremental(ctx)

    # Redis checkpoint should have been updated
    mock_redis.set.assert_called_once()
    # The saved checkpoint should be sequence_number=3 (the last row)
    call_args = mock_redis.set.call_args[0]
    assert int(call_args[1]) == 3


@pytest.mark.asyncio
async def test_incremental_verify_detects_tampering(db_session: AsyncSession):
    """
    If any row in the new batch has a mismatched hash, the incremental
    job must raise an exception (tamper alert).
    """
    # Row 1: clean
    log1 = _make_audit_log(sequence_number=1, prev_hash="0")
    db_session.add(log1)
    await db_session.flush()

    # Row 2: tampered payload but current_hash unchanged
    log2 = _make_audit_log(sequence_number=2, prev_hash=log1.current_hash)
    log2.payload = {"amount": 99999.0, "tampered": True}  # payload changed!
    db_session.add(log2)
    await db_session.flush()
    await db_session.commit()

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()

    ctx = {"session": db_session, "redis": mock_redis}

    with pytest.raises(Exception, match="[Tt]amper"):
        await verify_audit_chain_incremental(ctx)


# ---------------------------------------------------------------------------
# 4. verify_audit_chain_full job tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_verify_passes_clean_chain(db_session: AsyncSession):
    """
    Full scan should pass without raising for a clean chain.
    """
    prev_hash = "0"
    for i in range(1, 6):
        log = _make_audit_log(sequence_number=i, prev_hash=prev_hash)
        db_session.add(log)
        await db_session.flush()
        prev_hash = log.current_hash
    await db_session.commit()

    ctx = {"session": db_session}
    # Should not raise
    await verify_audit_chain_full(ctx)


@pytest.mark.asyncio
async def test_full_verify_detects_historical_tampering(db_session: AsyncSession):
    """
    Full scan must catch tampering in an early historical row (e.g., Row 2 of 5),
    even if all newer rows are untouched.
    """
    logs = []
    prev_hash = "0"
    for i in range(1, 6):
        log = _make_audit_log(sequence_number=i, prev_hash=prev_hash)
        db_session.add(log)
        await db_session.flush()
        prev_hash = log.current_hash
        logs.append(log)
    await db_session.commit()

    # Tamper with Row 2 (historical) — payload changed, current_hash untouched
    logs[1].payload = {"amount": 99999.0, "tampered": True}
    await db_session.flush()
    await db_session.commit()

    ctx = {"session": db_session}

    with pytest.raises(Exception, match="[Tt]amper"):
        await verify_audit_chain_full(ctx)


@pytest.mark.asyncio
async def test_full_verify_detects_broken_chain_link(db_session: AsyncSession):
    """
    Full scan must detect when a row's prev_hash doesn't match the previous
    row's current_hash (chain link is broken).
    """
    log1 = _make_audit_log(sequence_number=1, prev_hash="0")
    db_session.add(log1)
    await db_session.flush()

    # Row 2 has an incorrect prev_hash (doesn't link to Row 1)
    log2 = _make_audit_log(sequence_number=2, prev_hash="definitely_not_row1_hash")
    db_session.add(log2)
    await db_session.flush()
    await db_session.commit()

    ctx = {"session": db_session}

    with pytest.raises(Exception, match="[Tt]amper|[Cc]hain"):
        await verify_audit_chain_full(ctx)
