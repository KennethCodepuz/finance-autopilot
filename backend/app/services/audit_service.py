from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from sqlalchemy import select, func
import hashlib, json
from datetime import datetime, timezone

async def calculate_audit_hash(prev_audit_entry: AuditLog, session: AsyncSession, target_id: int, target_type: str, actor_id: str, action: str, actor_type: str):
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
         "target_id": str(target_id)
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