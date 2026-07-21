import plaid
from plaid.api import plaid_api
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