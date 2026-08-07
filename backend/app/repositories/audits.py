
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from sqlalchemy import select

async def get_last_audit_log(session: AsyncSession):
   try:
      last_audit = await session.execute(select(AuditLog).order_by(AuditLog.sequence_number.desc()).limit(1))
      return last_audit.scalars().first()
   except Exception as e:
      raise

async def get_audit_logs(offset: int, limit: int, actor_type: str | None, action: str | None, session: AsyncSession):
   try:
      query = select(AuditLog)
      filters = []
      
      if action:
         filters.append(AuditLog.action == action)
      
      if actor_type:
         filters.append(AuditLog.actor_type == actor_type)

      if filters:
         query = query.where(*filters)

      query = query.offset(offset).limit(limit).order_by(AuditLog.sequence_number.desc())
      audits = await session.execute(query)

      return audits.scalars().all()
   except Exception as e:
      raise