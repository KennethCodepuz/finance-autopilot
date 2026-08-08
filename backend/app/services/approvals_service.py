
from datetime import timezone
from datetime import datetime
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
from app.services.audit_service import create_and_verify_audit_log
import json

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

      audit_log = await create_and_verify_audit_log(session, audit_payload=ledger_entry.payload, target_id=ledger_entry.id, target_type="ledger", actor_id="human", action="proposal_approved", actor_type="human")
      
      event_data = {
         "event_type": "proposal.approved",
         "timestamp": datetime.now(timezone.utc).isoformat(),
         "payload": {
            "ledger_id": ledger_entry.id,
            "action_type": ledger_entry.action_type,
            "amount": ledger_entry.payload.get("amount") if isinstance(ledger_entry.payload, dict) else 0.0,
            "payee": ledger_entry.payload.get("payee") if isinstance(ledger_entry.payload, dict) else "",
            "account_id": ledger_entry.payload.get("account_id") if isinstance(ledger_entry.payload, dict) else 0,
            "risk_score": ledger_entry.risk_score,
            "risk_tier": ledger_entry.risk_tier,
            "status": "approved"
         }
      }
      await redis.publish("activity_feed", json.dumps(event_data))

      return {"message": "Action approved successfully", "audit_log_id": audit_log.id, "risk_tier": "high"}
   except Exception as e:
      await session.rollback()
      raise HTTPException(status_code=500, detail=str(e))


async def reject_proposal_action(ledger_id:int, session: AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   try:
      ledger_entry = await approvals_repository.get_ledger_entry_by_id(session=session, ledger_id=ledger_id)

      ledger_entry.status = "rejected"  
      await session.flush()
      
      audit_log = await create_and_verify_audit_log(session, audit_payload=ledger_entry.payload, target_id=ledger_entry.id, target_type="ledger", actor_id="human", action="proposal_rejected", actor_type="human")
      
      event_data = {
         "event_type": "proposal.rejected",
         "timestamp": datetime.now(timezone.utc).isoformat(),
         "payload": {
            "ledger_id": ledger_entry.id,
            "action_type": ledger_entry.action_type,
            "amount": ledger_entry.payload.get("amount") if isinstance(ledger_entry.payload, dict) else 0.0,
            "payee": ledger_entry.payload.get("payee") if isinstance(ledger_entry.payload, dict) else "",
            "account_id": ledger_entry.payload.get("account_id") if isinstance(ledger_entry.payload, dict) else 0,
            "risk_score": ledger_entry.risk_score,
            "risk_tier": ledger_entry.risk_tier,
            "status": "rejected"
         }
      }
      await redis.publish("activity_feed", json.dumps(event_data))

      return {"message": "Action rejected successfully", "audit_log_id": audit_log.id, "risk_tier": "high"}
   except Exception as e:
      await session.rollback()
      raise HTTPException(status_code=500, detail=str(e))

