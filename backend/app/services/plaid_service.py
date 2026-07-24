from app.main import logger
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from app.core.config import settings
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from app.models.account import Account
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from app.models.transaction import Transaction



async def get_accounts(db: AsyncSession):
   accounts = await db.execute(select(Account))
   return accounts.scalars().all()

async def get_transactions(db: AsyncSession):
   transactions = await db.execute(select(Transaction))
   return transactions.scalars().all()

def get_plaid_client() -> plaid_api.PlaidApi:
    """Initializes and returns the Plaid API client."""
    host = plaid.Environment.Sandbox
    if settings.plaid_env.lower() == "development":
        host = plaid.Environment.Development
    elif settings.plaid_env.lower() == "production":
        host = plaid.Environment.Production

    configuration = plaid.Configuration(
        host=host,
        api_key={
            'clientId': settings.plaid_client_id,
            'secret': settings.plaid_secret,
        }
    )

    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)

def create_link_token(user_id: str):
   client = get_plaid_client()
   request = LinkTokenCreateRequest(
     user=LinkTokenCreateRequestUser(
       client_user_id=user_id
     ),
     products=[Products("auth"), Products("transactions")],
     client_name="Finance Autopilot",
     language="en",
     country_codes=[CountryCode("US")],
   )

   response = client.link_token_create(request)
   return response.to_dict()



def exchange_public_token(public_token: str):
   client = get_plaid_client()
   request = ItemPublicTokenExchangeRequest(
      public_token=public_token
   )

   response = client.item_public_token_exchange(request)
   return response.to_dict()

async def sync_accounts(access_token: str, session: AsyncSession, item_id: str):
   client = get_plaid_client()

   try:
      request = AccountsBalanceGetRequest(access_token=access_token)
      response = client.accounts_balance_get(request)

      for pl_acc in response.accounts:
         check_db = select(Account).where(Account.plaid_account_id == pl_acc.account_id)
         result = await session.execute(check_db)
         db_account = result.scalar_one_or_none()

         if db_account:
            db_account.name = pl_acc.name
            db_account.official_name = pl_acc.official_name
            db_account.mask = pl_acc.mask
            db_account.balance_available = pl_acc.balances.available
            db_account.balance_current = pl_acc.balances.current
            db_account.iso_currency_code = pl_acc.balances.iso_currency_code or "USD"

         else:
            new_acc = Account(
               item_id=str(item_id),
               plaid_account_id = str(pl_acc.account_id),
               name = str(pl_acc.name),
               official_name = str(pl_acc.official_name),
               mask = str(pl_acc.mask),
               balance_available = pl_acc.balances.available,
               balance_current = pl_acc.balances.current,
               iso_currency_code = pl_acc.balances.iso_currency_code,
               type = str(pl_acc.type),
               subtype = str(pl_acc.subtype)
            )
            session.add(new_acc)

      await session.commit()
      return {"success": True}

   except Exception as e:
      await session.rollback()
      logger.error(f"Error syncing accounts: {e}")
      raise 

async def sync_transactions(access_token:str, session: AsyncSession):
   client = get_plaid_client()
   added, modified, removed = [], [], []
   has_more = True
   cursor = None

   try:

      while has_more:
         transaction = TransactionsSyncRequest(
            access_token=access_token, 
            cursor=cursor, 
            count=50
         )
         response = client.transactions_sync(transaction)
         added.extend(response.added)
         modified.extend(response.modified)
         removed.extend(response.removed)
         cursor = response.next_cursor
         has_more = response.has_more

      for pl_txn in added:
         result = await session.execute(
            select(Account).where(Account.plaid_account_id == pl_txn.account_id)
         )

         db_account = result.scalar_one_or_none()
         if db_account is None:
            continue

         account_id = db_account.id

         new_transaction = Transaction(
            account_id = account_id,
            plaid_transaction_id = pl_txn.transaction_id,
            amount = pl_txn.amount,
            date = pl_txn.date,
            name = pl_txn.name,
            merchant_name = pl_txn.merchant_name,
            category = ", ".join(pl_txn.category) if pl_txn.category else None,
            pending = pl_txn.pending,
            raw_payload = pl_txn.to_dict()
         )
         session.add(new_transaction)
   
      for pl_txn in modified:
         update_txn = select(Transaction).where(Transaction.plaid_transaction_id == pl_txn.transaction_id)
         result = await session.execute(update_txn)
         db_txn = result.scalar_one_or_none()

         if db_txn:
            db_txn.amount = pl_txn.amount
            db_txn.date = pl_txn.date
            db_txn.name = pl_txn.name
            db_txn.merchant_name = pl_txn.merchant_name
            db_txn.category = ", ".join(pl_txn.category) if pl_txn.category else None
            db_txn.pending = pl_txn.pending
            db_txn.raw_payload = pl_txn.to_dict()

      for pl_txn in removed:
         remove_txn = select(Transaction).where(Transaction.plaid_transaction_id == pl_txn.transaction_id)
         result = await session.execute(remove_txn)
         db_txn = result.scalar_one_or_none()

         if db_txn:
            await session.delete(db_txn)

      transactions_synced = len(added) + len(modified) - len(removed)

      await session.commit()

      return {"transactions_synced": transactions_synced}

   except Exception as e:
      await session.rollback()
      logger.error(f"Error syncing transactions: {e}")
      raise
      

