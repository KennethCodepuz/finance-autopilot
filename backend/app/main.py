from app.routes import audit
from arq.connections import RedisSettings
from arq import create_pool
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import plaid
from app.core.config import settings
from app.routes import agent
from app.routes import approvals
from app.routes import audit
from app.routes import plaid
from app.routes import websockets
from app.core.redis import parse_redis_settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
   app.state.redis = await create_pool(parse_redis_settings(settings.redis_url))
   
   yield 

   await app.state.redis.close()

app = FastAPI(
    title="Finance Autopilot",
    description="AI-powered financial agent with human-in-the-loop approval",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(plaid.router)
app.include_router(approvals.router)
app.include_router(audit.router)
app.include_router(websockets.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}
