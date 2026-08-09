"""
Database Seeding Script for Finance Autopilot — PostgreSQL

Populates your PostgreSQL database with realistic sample data:
1. Plaid Accounts (Checking & Savings)
2. Recent Transactions (Settled & Pending)
3. Pending Approval Proposals (High-risk items needing human intervention)
4. Cryptographically verified Audit Log chain entries

Run with:
  uv --directory backend run python seed.py
"""

import asyncio
from datetime import datetime, date, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.idempotency import IdempotencyKey
from app.models.ledger import OutboxLedger
from app.models.audit import AuditLog
from app.services.audit_service import create_and_verify_audit_log


async def seed():
    print(f"🌱 Connecting to PostgreSQL: {settings.database_url}")

    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Check or Create Accounts
        res_acc = await session.execute(select(Account))
        acc1 = res_acc.scalars().first()
        
        if not acc1:
            acc1 = Account(
                plaid_account_id="acc_plaid_checking_001",
                item_id="item_sandbox_001",
                name="Plaid Checking",
                official_name="Plaid Gold Checking Account",
                type="depository",
                subtype="checking",
                mask="0000",
                balance_available=110000.00,
                balance_current=110000.00,
                iso_currency_code="USD"
            )
            acc2 = Account(
                plaid_account_id="acc_plaid_savings_002",
                item_id="item_sandbox_001",
                name="Plaid Savings",
                official_name="Plaid High Yield Savings",
                type="depository",
                subtype="savings",
                mask="1111",
                balance_available=14580.00,
                balance_current=14580.00,
                iso_currency_code="USD"
            )
            session.add_all([acc1, acc2])
            await session.flush()
            print("  + Accounts created.")

        # 2. Check or Create Transactions
        res_tx = await session.execute(select(Transaction))
        if not res_tx.scalars().first():
            tx1 = Transaction(
                account_id=acc1.id,
                plaid_transaction_id="tx_001",
                amount=450.00,
                date=date(2024, 11, 26),
                name="Github Enterprise",
                merchant_name="Github Inc",
                category="Software & Cloud Services",
                pending=False
            )
            tx2 = Transaction(
                account_id=acc1.id,
                plaid_transaction_id="tx_002",
                amount=-2500.00,
                date=date(2024, 11, 28),
                name="Plaid Sync Transfer",
                merchant_name="Plaid Financial",
                category="Transfer",
                pending=False
            )
            tx3 = Transaction(
                account_id=acc1.id,
                plaid_transaction_id="tx_003",
                amount=-8400.00,
                date=date(2024, 11, 30),
                name="Stripe Merchant Settlement",
                merchant_name="Stripe Payments",
                category="Income",
                pending=False
            )
            tx4 = Transaction(
                account_id=acc1.id,
                plaid_transaction_id="tx_004",
                amount=1240.00,
                date=date(2024, 12, 5),
                name="AWS Cloud Hosting",
                merchant_name="Amazon Web Services",
                category="Infrastructure",
                pending=True
            )
            session.add_all([tx1, tx2, tx3, tx4])
            await session.flush()
            print("  + Transactions created.")

        # 3. Check or Create Pending Proposals
        res_prop = await session.execute(select(OutboxLedger))
        prop1 = res_prop.scalars().first()
        if not prop1:
            key1 = IdempotencyKey(
                key="idemp_key_proposal_001",
                endpoint="propose_action",
                request_hash="hash_001",
                status="completed",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            key2 = IdempotencyKey(
                key="idemp_key_proposal_002",
                endpoint="propose_action",
                request_hash="hash_002",
                status="completed",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            session.add_all([key1, key2])
            await session.flush()

            prop1 = OutboxLedger(
                idempotency_key_id=key1.id,
                idempotency_key=key1.key,
                action_type="transfer_funds",
                payload={"action_type": "transfer_funds", "amount": 12500.00, "payee": "Acme Logistics LLC", "account_id": acc1.id},
                status="pending",
                risk_score=85,
                risk_tier="high"
            )
            prop2 = OutboxLedger(
                idempotency_key_id=key2.id,
                idempotency_key=key2.key,
                action_type="wire_payment",
                payload={"action_type": "wire_payment", "amount": 45000.00, "payee": "Global Supplier Corp", "account_id": acc1.id},
                status="pending",
                risk_score=92,
                risk_tier="high"
            )
            session.add_all([prop1, prop2])
            await session.flush()
            print("  + Proposals created.")

        # 4. Check or Create Audit Logs
        res_audit = await session.execute(select(AuditLog))
        if not res_audit.scalars().first():
            prop_id = prop1.id if prop1 else 1
            acc_id = acc1.id if acc1 else 1

            await create_and_verify_audit_log(
                session=session,
                audit_payload={"action_type": "transfer_funds", "amount": 12500.00, "payee": "Acme Logistics LLC"},
                target_id=prop_id,
                target_type="ledger",
                actor_id="agent_autopilot_v1",
                action="proposal.created",
                actor_type="agent"
            )

            await create_and_verify_audit_log(
                session=session,
                audit_payload={"action_type": "wire_payment", "amount": 45000.00, "payee": "Global Supplier Corp"},
                target_id=prop_id,
                target_type="ledger",
                actor_id="agent_autopilot_v1",
                action="proposal.created",
                actor_type="agent"
            )

            await create_and_verify_audit_log(
                session=session,
                audit_payload={"action_type": "sync_accounts", "accounts_synced": 2},
                target_id=acc_id,
                target_type="account",
                actor_id="system_cron",
                action="plaid.synced",
                actor_type="system"
            )
            print("  + Audit logs created.")

        await session.commit()
        print("✅ PostgreSQL database seeding check completed!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
