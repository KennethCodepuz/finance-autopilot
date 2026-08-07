from app.routes import audit
from arq.connections import RedisSettings
from arq import create_pool
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import plaid
from app.core.config import settings
from app.routes import approvals

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
   app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
   
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
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plaid.router)
app.include_router(approvals.router)
app.include_router(audit.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}
