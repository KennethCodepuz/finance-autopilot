
from app.services.audit_service import calculate_audit_hash
from app.repositories.audits import get_last_audit_log
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

      prev_audit_entry = await get_last_audit_log(session)

      audit_log = await calculate_audit_hash(prev_audit_entry, session, ledger_entry.payload, ledger_entry.id, "ledger", "human", "proposal_approved", "human")

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

      prev_audit_entry = await get_last_audit_log(session)

      audit_log = await calculate_audit_hash(prev_audit_entry, session, ledger_entry.payload, ledger_entry.id, "ledger", "human", "proposal_rejected", "human")

      session.add(audit_log)
      await session.commit()
      return {"message": "Action rejected successfully"}
   except Exception as e:
      await session.rollback()
      raise HTTPException(status_code=500, detail=str(e))

