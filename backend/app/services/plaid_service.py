import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from app.core.config import settings


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