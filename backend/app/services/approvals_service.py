
from app.models import AuditLog
from fastapi import HTTPException
from app.schemas.approvals import ActionProposalRequest, ActionProposalResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis import get_redis
from fastapi import Depends
from app.repositories import approvals as approvals_repository
from arq import ArqRedis
from app.services.agent_service import propose_action
import hashlib, json
from sqlalchemy import select, func

async def propose_action_to_agent(request: ActionProposalRequest, session: AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)  ):

   try:
      response = await propose_action(request.action_type, request.amount, request.payee, request.account_id, session, redis)
      reponse_payload = ActionProposalResponse(
         ledger_id = response.id,
         risk_score = response.risk_score,
         tier = response.risk_tier,
         status = response.status,
      )
      return reponse_payload
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

async def fetch_pending_approvals(session: AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   try:
      response = await approvals_repository.get_pending_approvals(session)
      return response
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

async def approve_proposal_action(ledger_id: int, session: AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   try:
      ledger_entry = await approvals_repository.get_ledger_entry_by_id(session=session, ledger_id=ledger_id)

      if ledger_entry is None:
         raise HTTPException(status_code=404, detail="Ledger entry not found")
      
      if ledger_entry.status != "pending" or ledger_entry.risk_tier   != "high":
         raise HTTPException(status_code=400, detail="Action is not pending for human approval")
      
      await redis.enqueue_job("execute_ledger_entry", ledger_entry.id)
      await session.flush()

      max_seq_req = await session.execute(select(func.max(AuditLog.sequence_number)))
      max_seq = (max_seq_req.scalar_one_or_none() or 0) + 1

      audit_log = AuditLog(
         actor_type="human",
         sequence_number=max_seq,
         actor_id="human_default",
         action="action_approved",
         target_id=str(ledger_entry.id),
         payload=ledger_entry.payload,
         current_hash=hashlib.sha256(json.dumps(ledger_entry.payload).encode()).hexdigest(),
         prev_hash=ledger_entry.idempotency_key,
      )

      session.add(audit_log)
      await session.commit()

      return {"message": "Action approved successfully"}
   except Exception as e:
      await session.rollback()
      raise HTTPException(status_code=500, detail=str(e))


async def reject_proposal_action(ledger_id:int, session: AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   try:
      ledger_entry = await approvals_repository.get_ledger_entry_by_id(session=session, ledger_id=ledger_id)

      ledger_entry.status = "rejected"  

      max_seq_req = await session.execute(select(func.max(AuditLog.sequence_number)))
      max_seq = (max_seq_req.scalar_one_or_none() or 0) + 1

      audit_log = AuditLog(
         actor_type="human",
         sequence_number=max_seq,
         actor_id="human_default",
         action="action_rejected",
         target_id=str(ledger_entry.id),
         payload=ledger_entry.payload,
         current_hash=hashlib.sha256(json.dumps(ledger_entry.payload).encode()).hexdigest(),
         prev_hash=ledger_entry.idempotency_key,
      )

      session.add(audit_log)
      await session.commit()
      return {"message": "Action rejected successfully"}
   except Exception as e:
      await session.rollback()
      raise HTTPException(status_code=500, detail=str(e))

