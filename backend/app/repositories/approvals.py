from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ledger import OutboxLedger
from sqlalchemy import select

async def get_pending_approvals(session: AsyncSession):
   response = await session.execute(select(OutboxLedger).where(OutboxLedger.status == "pending"))
   return response.scalars().all()
   
async def get_ledger_entry_by_id(session: AsyncSession, ledger_id: int):
   response = await session.execute(select(OutboxLedger).where(OutboxLedger.id == ledger_id))
   return response.scalars().first()
