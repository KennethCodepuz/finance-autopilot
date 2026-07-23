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

