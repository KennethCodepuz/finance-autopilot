from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


# Request Schemas

class PublicTokenExchangeRequest(BaseModel):
    public_token: str


# Response Schemas 

class LinkTokenCreateResponse(BaseModel):
    link_token: str
    expiration: str


class PublicTokenExchangeResponse(BaseModel):
    access_token: str
    item_id: str

class SyncRequest(BaseModel):
    access_token: str
    item_id: str


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plaid_account_id: str
    name: str
    official_name: Optional[str] = None
    type: str
    subtype: Optional[str] = None
    mask: Optional[str] = None
    balance_available: Optional[float] = None
    balance_current: Optional[float] = None
    iso_currency_code: str


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    plaid_transaction_id: str
    amount: float
    date: date
    name: str
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    pending: bool


class SyncResponse(BaseModel):
    accounts_synced: int
    transactions_synced: int

