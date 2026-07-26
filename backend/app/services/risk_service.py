
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.transaction import Transaction
from sqlalchemy import select


async def calculate_risk_score(action_type, amount, payee, session: AsyncSession):
   score = 0
   factors = []


   if amount > 500:
      score += 7
      factors.append("amount > 500: +7")
   if amount > 2000 :
      score += 5
      factors.append("amount > 2000: +5")
   if action_type == "transfer":
      score += 5
      factors.append("action_type is transfer: +5")
   if action_type == "bill_pay":
      score += 3
      factors.append("action_type is bill_pay: +3")

   response = await session.execute(
      select(Transaction).where(Transaction.merchant_name == payee)
   )

   if response.scalars().first() is None:
      score += 8
      factors.append("Payee is new: +8")

   if score <= 9:
      return {"score": score,"tier": "low", "factors": factors}
   else:
      return {"score": score,"tier": "high", "factors": factors}

   
   

   