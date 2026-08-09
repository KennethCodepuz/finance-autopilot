from fastapi import HTTPException
from fastapi import Query
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import audits as audits_repository
from app.core.database import get_db
from app.services.audit_service import recompute_hash

router = APIRouter(prefix="/api/audit", tags=["Audit"])

@router.get("/logs")
async def get_audit_logs(offset: int = Query(default = 0, ge = 0), limit: int = Query(default = 10, ge = 1, le = 100), actor_type: str | None = None, action: str | None = None, db: AsyncSession = Depends(get_db)):

   try:
      audits_response = await audits_repository.get_audit_logs(offset, limit, actor_type, action, db)
      audit_logs = []

      if audits_response is None:
         return audit_logs
      
      for audit in audits_response:
         recomputed_hash = recompute_hash(audit)
         is_verified = audit.current_hash == recomputed_hash

        
         audit_logs.append({
            "id": audit.id,
            "sequence_number": audit.sequence_number,
            "timestamp": audit.timestamp,
            "prev_hash": audit.prev_hash,
            "current_hash": audit.current_hash,
            "actor_id": audit.actor_id,
            "actor_type": audit.actor_type,
            "action": audit.action,
            "target_type": audit.target_type,
            "target_id": audit.target_id,
            "payload": audit.payload.get("payload"),
            "is_verified": is_verified
         })
   
      return audit_logs
   except Exception as e:
      raise HTTPException(status_code = 500, detail = str(e))