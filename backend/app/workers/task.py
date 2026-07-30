from app.core.database import AsyncSessionLocal
from app.models import IdempotencyKey, AuditLog, OutboxLedger
from sqlalchemy import select
import hashlib, json
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

      max_seq_req = await session.execute(select(func.max(AuditLog.sequence_number)))
      max_seq = (max_seq_req.scalar_one_or_none() or 0) + 1

      audit_log = AuditLog(
         actor_type="agent",
         sequence_number=max_seq,
         actor_id="agent_default",
         action="transaction_executed",
         target_id=str(ledger_entry.id),
         payload=ledger_entry.payload,
         current_hash=hashlib.sha256(json.dumps(ledger_entry.payload).encode()).hexdigest(),
         prev_hash=db_key.request_hash,
      )

      session.add(audit_log)

      await session.commit()
   except Exception as e:
      await session.rollback()
      raise
   finally:
      if should_close:
         await session.close()
      
