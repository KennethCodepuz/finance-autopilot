from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class ActionProposalRequest(BaseModel):
    action_type: str
    amount: float
    payee: str
    account_id: int

class ActionProposalResponse(BaseModel):
    ledger_id: int
    risk_score: int
    tier: str
    status: str

class PendingApprovalItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: str
    amount: float
    payee: str
    risk_score: int
    status: str
    created_at: datetime