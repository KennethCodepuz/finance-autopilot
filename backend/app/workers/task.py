
from app.services.audit_service import recompute_hash
from app.models import AuditLog
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
      
async def verify_audit_chain_full(ctx: dict):
   
   session = ctx.get("session")
   should_close = False

   if not session:
      session = AsyncSessionLocal()
      should_close = True

   try:
      all_audit_logs = await session.execute(select(AuditLog).order_by(AuditLog.sequence_number.asc()))
      current_audit_sequence = 0
      rows = all_audit_logs.scalars().all()
      
      if not rows:
         return
      
      if current_audit_sequence == 0:
         expected_prev_hash = "0"
      
      for log in rows:
         recomputed_hash = recompute_hash(log)
         if log.current_hash != recomputed_hash:
            raise ValueError(f"Tamper detected: chain link broken at sequence_number {log.sequence_number}")

         if log.prev_hash != expected_prev_hash:
            raise ValueError(f"Tamper detected: chain link broken at sequence_number {log.sequence_number}")
         
         expected_prev_hash = log.current_hash
         current_audit_sequence = log.sequence_number
      
      return True
   except Exception as e:
      await session.rollback()
      raise
   finally:
      if should_close:
         await session.close()

async def verify_audit_chain_incremental(ctx: dict):
   
   session = ctx.get("session")
   redis = ctx.get("redis")
   should_close = False

   if not session:
      session = AsyncSessionLocal()
      should_close = True
   
   try:
      checkpoint = await redis.get("audit_checkpoint")
      if checkpoint is None:
         checkpoint = 0
      
      audit_logs = await session.execute(
         select(AuditLog).where(AuditLog.sequence_number > checkpoint)
      )

      if audit_logs.scalars().first() is None:
         return 

      if checkpoint == 0:  
         expected_prev_hash = "0"
      else:
         current_row = await session.execute(
            select(AuditLog).where(AuditLog.sequence_number == checkpoint)
         )
         expected_prev_hash = current_row.scalars().first().current_hash
   
      next_audit_logs = await session.execute(
         select(AuditLog).where(AuditLog.sequence_number > checkpoint)
      )


      for log in next_audit_logs.scalars():
         computed_hash = recompute_hash(log)
         if log.current_hash != computed_hash:
            raise ValueError("Tamper detected: chain link broken at sequence_number X")
         expected_prev_hash = log.current_hash
         checkpoint = log.sequence_number


      await redis.set("audit_checkpoint", checkpoint)
   except Exception as e:
      await session.rollback()
      raise
   finally:
      if should_close:
         await session.close()
      
      
      
      


