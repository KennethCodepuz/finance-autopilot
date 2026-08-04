
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from sqlalchemy import select, func
import hashlib, json
from datetime import datetime, timezone
from app.repositories.audits import get_last_audit_log

async def calculate_audit_hash(prev_audit_entry: AuditLog, session: AsyncSession, audit_payload: dict, target_id: int, target_type: str, actor_id: str, action: str, actor_type: str):
   try:
      if prev_audit_entry:
         prev_hash = prev_audit_entry.current_hash
      else:
         prev_hash = "0"
      
      now = datetime.now(timezone.utc)

      max_seq_req = await session.execute(select(func.max(AuditLog.sequence_number)))
      max_seq = (max_seq_req.scalar_one_or_none() or 0) + 1

      payload = {
         "sequence_number": max_seq,
         "timestamp": now.isoformat(),
         "prev_hash": prev_hash,
         "actor_id": actor_id,
         "actor_type": actor_type,
         "action": action,
         "target_type": target_type,
         "target_id": str(target_id),
         "payload": audit_payload,
      }
      
      audit_log = AuditLog(
         actor_type=actor_type,
         sequence_number=max_seq,
         timestamp=now,
         actor_id=actor_id,
         action=action,
         target_type=target_type,
         target_id=str(target_id),
         payload=payload,
         current_hash=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
         prev_hash=prev_hash,
      )
      return audit_log
   except Exception as e:
      raise

def recompute_hash(audit_log: AuditLog):
   try:
      payload = {
         "sequence_number": audit_log.sequence_number,
         "timestamp": audit_log.timestamp.isoformat(),
         "prev_hash": audit_log.prev_hash,
         "actor_id": audit_log.actor_id,
         "actor_type": audit_log.actor_type,
         "action": audit_log.action,
         "target_type": audit_log.target_type,
         "target_id": audit_log.target_id,
         "payload": audit_log.payload.get("payload"),
      }
      
      return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
   except Exception as e:
      raise ValueError("Failed to recompute hash") 

async def create_and_verify_audit_log(session: AsyncSession, audit_payload: dict, target_id: int, target_type: str, actor_id: str, action: str, actor_type: str):
   try:
      prev_audit_entry = await get_last_audit_log(session)

      if prev_audit_entry is not None:
         if prev_audit_entry.current_hash != recompute_hash(prev_audit_entry):
            raise ValueError("Invalid audit chain")
      
      audit_log = await calculate_audit_hash(prev_audit_entry, session, audit_payload, target_id, target_type, actor_id, action, actor_type)

      session.add(audit_log)
      await session.flush()

      recomputed_hash = recompute_hash(audit_log)

      if audit_log.current_hash != recomputed_hash:
         raise ValueError("Audit log has been tampered") 

      await session.commit()
      return audit_log
   except Exception as e:
      await session.rollback()
      raise 