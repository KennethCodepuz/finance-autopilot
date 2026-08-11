from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from arq import ArqRedis

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.agent import AgentPromptRequest, AgentPromptResponse
from app.services.llm_service import run_agent_prompt, AGENT_TOOLS

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/prompt", response_model=AgentPromptResponse)
async def process_agent_prompt(
    request: AgentPromptRequest,
    session: AsyncSession = Depends(get_db),
    redis: ArqRedis = Depends(get_redis),
):
    """Submits a natural language prompt to the AI Agent for tool evaluation and execution."""
    try:
        response = await run_agent_prompt(
            prompt=request.prompt,
            session=session,
            redis=redis,
            account_id_filter=request.account_id,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent prompt processing failed: {str(e)}")


@router.get("/tools")
async def list_agent_tools():
    """Lists available tools accessible by the LLM agent."""
    return {"tools": AGENT_TOOLS}
