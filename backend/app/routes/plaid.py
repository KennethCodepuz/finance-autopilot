from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.schemas.plaid import PublicTokenExchangeRequest, SyncRequest
from fastapi import APIRouter
from app.services import plaid_service as ps


router = APIRouter(prefix="/api/plaid", tags=["Plaid"])


@router.post("/create-link-token")
async def create_link_token():
   user = ps.create_link_token(user_id="user_default")
   return user

@router.post("/exchange-public-token")
async def exchange_public_token(body: PublicTokenExchangeRequest):
   public_token_response = ps.exchange_public_token(body.public_token)
   return public_token_response

@router.post("/sync")
async def sync(sync_request: SyncRequest, db: AsyncSession = Depends(get_db)):
   sync_status = await ps.sync_accounts(sync_request.access_token, db, sync_request.item_id)
   sync_transactions = await ps.sync_transactions(sync_request.access_token, db)
   return [sync_status, sync_transactions]

@router.get("/accounts")
async def get_accounts(db: AsyncSession = Depends(get_db)):
   accounts = await ps.get_accounts(db)
   return accounts

@router.get("/transactions")
async def get_transactions(db: AsyncSession = Depends(get_db)):
   transactions = await ps.get_transactions(db)
   return transactions

@router.post("/sandbox/create-token")
async def create_sandbox_public_token():
   token = await ps.create_sandbox_public_token()
   return token