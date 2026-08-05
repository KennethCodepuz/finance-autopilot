# Tech Stack

**Related:** [[Architecture Vision]], [[Decisions Log]]

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (App Router, TypeScript) |
| Financial data | Plaid Sandbox |
| Backend | Python + FastAPI |
| Database | PostgreSQL + SQLAlchemy (async) |
| Queue / Jobs | ARQ + Redis |
| Containerisation | Docker |
| Deployment | Render |
| Idempotency | UUID + DB unique constraint |
| Audit storage | Append-only table + Hash chaining + ARQ verification job |
| Execution boundary | Internal ledger (Outbox pattern) |
