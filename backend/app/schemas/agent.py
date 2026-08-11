from typing import Any, Optional
from pydantic import BaseModel, Field


class AgentPromptRequest(BaseModel):
    prompt: str = Field(..., description="Natural language prompt for the financial agent", min_length=1)
    account_id: Optional[int] = Field(None, description="Optional account ID filter context")


class ToolCallResult(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    status: str
    message: str
    ledger_id: Optional[int] = None
    risk_tier: Optional[str] = None


class AgentPromptResponse(BaseModel):
    prompt: str
    agent_thought: str
    tools_called: list[ToolCallResult] = []
    summary: str
