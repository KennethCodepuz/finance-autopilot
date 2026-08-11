from datetime import date
from unittest.mock import AsyncMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.transaction import Transaction
from app.services.llm_service import (
    AGENT_TOOLS,
    execute_agent_tool,
    run_agent_prompt,
)


@pytest.mark.asyncio
async def test_agent_tools_listing():
    assert len(AGENT_TOOLS) == 3
    tool_names = [t["function"]["name"] for t in AGENT_TOOLS]
    assert "categorize_transaction" in tool_names
    assert "transfer_funds" in tool_names
    assert "flag_anomaly" in tool_names


@pytest.mark.asyncio
async def test_execute_categorize_transaction(db_session: AsyncSession):
    # Setup test account and transaction
    acc = Account(
        plaid_account_id="acc_123",
        item_id="item_123",
        name="Checking",
        type="depository",
        balance_current=1000.0,
    )
    db_session.add(acc)
    await db_session.flush()

    tx = Transaction(
        account_id=acc.id,
        plaid_transaction_id="tx_123",
        amount=45.50,
        date=date(2026, 8, 11),
        name="Coffee Shop",
        category="General",
    )
    db_session.add(tx)
    await db_session.flush()

    mock_redis = AsyncMock()

    res = await execute_agent_tool(
        name="categorize_transaction",
        args={"transaction_id": tx.id, "category": "Dining"},
        session=db_session,
        redis=mock_redis,
    )

    assert res.status == "executed"
    assert "Dining" in res.message
    assert tx.category == "Dining"
    assert mock_redis.publish.called


@pytest.mark.asyncio
async def test_execute_categorize_nonexistent_transaction(db_session: AsyncSession):
    mock_redis = AsyncMock()

    res = await execute_agent_tool(
        name="categorize_transaction",
        args={"transaction_id": 999999, "category": "Dining"},
        session=db_session,
        redis=mock_redis,
    )

    assert res.status == "error"
    assert "not found" in res.message.lower()


@pytest.mark.asyncio
async def test_execute_transfer_funds_low_risk(db_session: AsyncSession):
    acc = Account(
        plaid_account_id="acc_456",
        item_id="item_456",
        name="Savings",
        type="depository",
        balance_current=5000.0,
    )
    db_session.add(acc)
    await db_session.flush()

    # Existing transaction so merchant "Savings" is not new (+0 pts)
    tx = Transaction(
        account_id=acc.id,
        plaid_transaction_id="tx_456",
        amount=10.0,
        date=date(2026, 8, 11),
        name="Savings Transfer",
        merchant_name="Savings",
    )
    db_session.add(tx)
    await db_session.flush()

    mock_redis = AsyncMock()

    # Small transfer amount (< $500) to known payee "Savings" -> Low risk (5 pts <= 9)
    res = await execute_agent_tool(
        name="transfer_funds",
        args={"amount": 100.0, "payee": "Savings", "account_id": acc.id},
        session=db_session,
        redis=mock_redis,
    )

    assert res.status == "proposed"
    assert res.ledger_id is not None
    assert res.risk_tier == "low"
    assert mock_redis.enqueue_job.called


@pytest.mark.asyncio
async def test_execute_transfer_funds_high_risk(db_session: AsyncSession):
    mock_redis = AsyncMock()

    # Large transfer amount (> $500) -> High risk
    res = await execute_agent_tool(
        name="transfer_funds",
        args={"amount": 750.0, "payee": "External Payee", "account_id": 1},
        session=db_session,
        redis=mock_redis,
    )

    assert res.status == "proposed"
    assert res.ledger_id is not None
    assert res.risk_tier == "high"


@pytest.mark.asyncio
async def test_execute_flag_anomaly_tool(db_session: AsyncSession):
    acc = Account(
        plaid_account_id="acc_789",
        item_id="item_789",
        name="Credit Card",
        type="credit",
        balance_current=200.0,
    )
    db_session.add(acc)
    await db_session.flush()

    tx = Transaction(
        account_id=acc.id,
        plaid_transaction_id="tx_789",
        amount=899.99,
        date=date(2026, 8, 11),
        name="Unknown Tech Store",
        merchant_name="Unknown Tech Store",
    )
    db_session.add(tx)
    await db_session.flush()

    mock_redis = AsyncMock()

    res = await execute_agent_tool(
        name="flag_anomaly",
        args={"transaction_id": tx.id, "reason": "Unusual high purchase amount"},
        session=db_session,
        redis=mock_redis,
    )

    assert res.status == "proposed"
    assert res.ledger_id is not None
    assert "flagged" in res.message.lower()


@pytest.mark.asyncio
async def test_execute_unknown_tool(db_session: AsyncSession):
    mock_redis = AsyncMock()

    res = await execute_agent_tool(
        name="unknown_action",
        args={},
        session=db_session,
        redis=mock_redis,
    )

    assert res.status == "error"
    assert "unknown tool" in res.message.lower()


@pytest.mark.asyncio
async def test_run_agent_prompt_transfer_fallback(db_session: AsyncSession):
    mock_redis = AsyncMock()

    prompt_response = await run_agent_prompt(
        prompt="Please move $600 to my savings account for rent.",
        session=db_session,
        redis=mock_redis,
    )

    assert prompt_response.prompt == "Please move $600 to my savings account for rent."
    assert len(prompt_response.tools_called) >= 1
    tool_res = prompt_response.tools_called[0]
    assert tool_res.tool_name == "transfer_funds"
    assert tool_res.arguments["amount"] == 600.0


@pytest.mark.asyncio
async def test_run_agent_prompt_categorize_fallback(db_session: AsyncSession):
    acc = Account(
        plaid_account_id="acc_cat",
        item_id="item_cat",
        name="Checking",
        type="depository",
        balance_current=500.0,
    )
    db_session.add(acc)
    await db_session.flush()

    tx = Transaction(
        account_id=acc.id,
        plaid_transaction_id="tx_cat",
        amount=15.0,
        date=date(2026, 8, 11),
        name="Pizzeria",
        category="General",
    )
    db_session.add(tx)
    await db_session.flush()

    mock_redis = AsyncMock()

    prompt_response = await run_agent_prompt(
        prompt="Categorize transaction as Dining",
        session=db_session,
        redis=mock_redis,
    )

    assert len(prompt_response.tools_called) >= 1
    assert prompt_response.tools_called[0].tool_name == "categorize_transaction"
