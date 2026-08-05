import arq.connections

from app.core.config import settings
from app.workers.task import execute_ledger_entry, verify_audit_chain_full, verify_audit_chain_incremental


async def startup(ctx: dict) -> None:
    """Runs once when the worker starts."""
    pass


async def shutdown(ctx: dict) -> None:
    """Runs once when the worker shuts down."""
    pass

class WorkerSettings:
    """ARQ worker configuration."""
    functions = [execute_ledger_entry, verify_audit_chain_full, verify_audit_chain_incremental]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = arq.connections.RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5 minutes
