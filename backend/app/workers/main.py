import arq.connections

from app.core.config import settings
from app.workers.task import execute_ledger_entry, verify_audit_chain_full, verify_audit_chain_incremental
from arq import cron


async def startup(ctx: dict) -> None:
    """Runs once when the worker starts."""
    
    pass


async def shutdown(ctx: dict) -> None:
    """Runs once when the worker shuts down."""
    pass

class WorkerSettings:
    """ARQ worker configuration."""
    functions = [execute_ledger_entry, verify_audit_chain_full, verify_audit_chain_incremental]
    cron_jobs = [
        cron(verify_audit_chain_incremental, minute=0),
        cron(verify_audit_chain_full, hour=2, minute=0),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = arq.connections.RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 1
    job_timeout = 300  # 5 minutes
