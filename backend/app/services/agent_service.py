

from datetime import timedelta
from datetime import timezone
from datetime import datetime
from app.models import IdempotencyKey
from arq import ArqRedis
from app.services.risk_service import calculate_risk_score
from app.models.ledger import OutboxLedger
from sqlalchemy.ext.asyncio import AsyncSession
import uuid, hashlib, json
from app.services.audit_service import create_and_verify_audit_log


async def propose_action(action_type, amount, payee, account_id, session: AsyncSession, redis: ArqRedis):

   try:
      risk_score = await calculate_risk_score(action_type, amount, payee, session)
      payload = {
         "action_type": action_type,
         "amount": amount,
         "payee": payee,
         "account_id": account_id,
      }

      idempotency_key = IdempotencyKey(
         key=str(uuid.uuid4()),
         endpoint="propose action",
         request_hash=str(hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()),
         response_payload=None,
         status="processing",
         expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
      )

      ledger_entry = OutboxLedger(
         action_type=action_type,
         idempotency_key=idempotency_key.key,
         payload=payload,
         risk_score=risk_score["score"],
         risk_tier=risk_score["tier"],
      )

      session.add(idempotency_key)
      session.add(ledger_entry)
      await session.flush()

      await create_and_verify_audit_log(session, audit_payload=payload, target_id=ledger_entry.id, target_type="ledger", actor_id="agent_default", action="proposal.created", actor_type="agent")

      if risk_score["tier"] == "low":
         await redis.enqueue_job("execute_ledger_entry", ledger_entry.id)
      
      if risk_score["tier"] == "high":
         """ Await Human Approval """
         pass
         
      return ledger_entry
   except Exception as e:
      await session.rollback()
      raise 

   
   