from app.services.audit_service import calculate_audit_hash
from app.core.database import AsyncSessionLocal
from app.models import IdempotencyKey, AuditLog, OutboxLedger
from sqlalchemy import select
import hashlib, json
from app.repositories.audits import get_last_audit_log
from sqlalchemy import func

async def execute_ledger_entry(ctx: dict, ledger_id: int):
   ledger_entry = None

   session = ctx.get("session")
   should_close = False

   if not session:
      session = AsyncSessionLocal()
      should_close = True

   try:
      response = await session.execute(
         select(OutboxLedger).where(OutboxLedger.id == ledger_id)
      )
         
      ledger_entry = response.scalars().first()

      if ledger_entry is None:
         return

      if ledger_entry.status != "pending":
         return

      ledger_entry.status = "processing"
      await session.flush()

      print("Success")

      ledger_entry.status = "confirmed"
      idempotency_key_response = await session.execute(
         select(IdempotencyKey).where(IdempotencyKey.id == ledger_entry.idempotency_key_id)
      )
      db_key = idempotency_key_response.scalars().first()

      if db_key is None:
         return

      db_key.status = "completed"

      await session.flush()

      prev_audit_entry = await get_last_audit_log(session)

      audit_log = await calculate_audit_hash(prev_audit_entry, session, ledger_entry.payload, ledger_entry.id, "ledger", "agent_default", "ledger_entry.confirmed", "agent")

      session.add(audit_log)

      await session.commit()
   except Exception as e:
      await session.rollback()
      raise
   finally:
      if should_close:
         await session.close()
      
