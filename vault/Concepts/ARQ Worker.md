# ARQ Worker

**Related modules:** [[Task]], [[Workers Main]]

## What it is
ARQ is an async job queue backed by Redis. Workers are started separately
from FastAPI and process jobs from the queue.

## Worker functions
| Function | Trigger | Purpose |
|----------|---------|---------|
| `execute_ledger_entry` | Enqueued by `propose_action` | Executes confirmed actions |
| `verify_audit_chain_incremental` | Cron: every hour at :00 | Verifies new audit rows since checkpoint |
| `verify_audit_chain_full` | Cron: daily at 02:00 | Full chain scan from Row 1 |

## WorkerSettings
Defined in `app/workers/main.py`:
- `max_jobs = 1` — audit jobs must not run concurrently
- `job_timeout = 300` — 5 minute ceiling per execution

## Start the worker
```bash
arq app.workers.main.WorkerSettings
```
