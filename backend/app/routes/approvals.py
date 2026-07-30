import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from arq import ArqRedis

from app.core.database import get_db
from app.core.redis import get_redis
from app.models.ledger import OutboxLedger
from app.models.audit import AuditLog
from app.schemas.approvals import ActionProposalRequest, ActionProposalResponse, PendingApprovalItem
from app.repositories import approvals as approvals_repository
from app.services import approvals_service as approvals_service

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

@router.post("/propose")
async def propose_action(request: ActionProposalRequest, db:AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   return await approvals_service.propose_action_to_agent(request, db, redis)

@router.get("/pending-approvals")
async def get_approvals(db:AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   return await approvals_service.fetch_pending_approvals(db, redis)


@router.post("/approve/{ledger_id}")
async def approve_action(ledger_id:int, db:AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   return await approvals_service.approve_proposal_action(ledger_id, db, redis)


@router.post("/reject/{ledger_id}")
async def reject_action(ledger_id:int, db:AsyncSession = Depends(get_db), redis: ArqRedis = Depends(get_redis)):
   response = await approvals_service.reject_proposal_action(ledger_id, db, redis)
   return response