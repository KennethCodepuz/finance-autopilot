
from app.core.database import AsyncSessionLocal
from app.models import IdempotencyKey, OutboxLedger
from sqlalchemy import select
from app.services.audit_service import create_and_verify_audit_log


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

      audit_log = await create_and_verify_audit_log(session, audit_payload=ledger_entry.payload, target_id=ledger_entry.id, target_type="ledger", actor_id="agent_default", action="ledger_entry.confirmed", actor_type="agent")

      return audit_log
   except Exception as e:
      await session.rollback()
      raise
   finally:
      if should_close:
         await session.close()
      
