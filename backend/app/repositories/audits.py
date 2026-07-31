
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from sqlalchemy import select

async def get_last_audit_log(session: AsyncSession):
   try:
      last_audit = await session.execute(select(AuditLog).order_by(AuditLog.sequence_number.desc()).limit(1))
      return last_audit.scalars().first()
   except Exception as e:
      raise
