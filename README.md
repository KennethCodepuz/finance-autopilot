# Finance Autopilot

An AI-powered personal finance agent that connects to real financial data via Plaid Sandbox and proposes or executes actions — categorizing transactions, flagging anomalies, moving money between accounts — through tool calls. Built with a human-in-the-loop approval workflow so every consequential action requires explicit sign-off before execution.

---

## Architecture Decisions

Every core design decision in this project was reasoned through before writing code. The full decisions log is in [`architecture.md`](./architecture.md). Key choices:

| Decision | Choice | Why |
|----------|--------|-----|
| Idempotency | UUID + DB unique constraint | Two-hop protection (client→backend, backend→Plaid). Silent replay on retry. |
| Approval workflow | ARQ + Redis job queue | Clean separation of concerns. Denial signals agent to propose alternatives. Dead-lettered after N denials. |
| Audit trail | Append-only + Hash chaining | Tamper-evident by math — any edit or deletion breaks the chain, detectable by a background verification job. |
| Execution boundary | Internal ledger (Outbox pattern) | DB written first as `pending`. Plaid is not the source of truth. |
| Risk classification | Deterministic scoring rubric | Hard rules define point thresholds. LLM escalation path wired in but not called until the rubric demonstrably misses things. |
| Credential handling | `.env` local + Render env vars in production | Secrets never in code or version control. |

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 16 (App Router, TypeScript) |
| Backend | Python + FastAPI |
| Database | PostgreSQL + SQLAlchemy (async) |
| Migrations | Alembic |
| Queue / Workers | ARQ + Redis |
| Containerization | Docker + Docker Compose |
| Deployment | Render |
| Financial data | Plaid Sandbox |
| Real-time feed | WebSockets |
| Package managers | `uv` (Python) · `pnpm` (Node) |

---

## Required Screens

- **Accounts overview** — live balances and recent transactions from Plaid Sandbox
- **Pending approvals queue** — every action awaiting human sign-off, with approve/deny controls that resume agent execution
- **Audit trail viewer** — chronological, filterable, tamper-evident history of every action with reasoning attached
- **Agent activity feed** — live view via WebSocket of what the agent is currently proposing or doing

---

## Project Structure

```
finance-autopilot/
├── backend/
│   ├── app/
│   │   ├── core/          # Config (Pydantic settings) + DB engine
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # FastAPI routers
│   │   ├── services/      # Business logic (risk scorer, ledger, agent)
│   │   ├── workers/       # ARQ job definitions
│   │   └── main.py        # FastAPI app entry point
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/              # Next.js App Router
├── docker-compose.yml     # FastAPI + PostgreSQL + Redis + Worker
├── .env.example           # Required environment variables (no values)
└── architecture.md        # Full decisions log
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [pnpm](https://pnpm.io/) — Node package manager
- A [Plaid](https://dashboard.plaid.com/signup) account (free sandbox)

### 1. Clone and configure

```bash
git clone https://github.com/KennethCodepuz/finance-autopilot.git
cd finance-autopilot

# Copy the env template and fill in your values
cp .env.example .env
```

Required values in `.env`:

```bash
POSTGRES_PASSWORD=        # any local password
SECRET_KEY=               # openssl rand -hex 32
PLAID_CLIENT_ID=          # from Plaid dashboard
PLAID_SECRET=             # from Plaid dashboard (sandbox key)
OPENAI_API_KEY=           # your LLM API key
```

### 2. Start all services with Docker

```bash
docker compose up --build
```

This starts:
- **FastAPI backend** at `http://localhost:8000`
- **ARQ worker** (background job processor)
- **PostgreSQL** at `localhost:5432`
- **Redis** at `localhost:6379`

API docs available at `http://localhost:8000/api/docs`

### 3. Start the frontend

```bash
pnpm --dir frontend run dev
```

Frontend available at `http://localhost:3000`

---

## Development

### Backend (without Docker)

```bash
# Install dependencies
uv --directory backend sync

# Run migrations
uv --directory backend run alembic upgrade head

# Start the API server
uv --directory backend run uvicorn app.main:app --reload

# Start the worker (separate terminal)
uv --directory backend run python -m arq app.workers.main.WorkerSettings
```

### Frontend

```bash
pnpm --dir frontend run dev    # dev server
pnpm --dir frontend run build  # production build
pnpm --dir frontend run lint   # lint
```

### Running Tests

```bash
uv --directory backend run pytest
```

---

## Hard Constraints

These are non-negotiable regardless of how a feature is built:

1. Any state-changing tool call must be **safe to retry** — idempotency keys at every hop.
2. Actions above the risk threshold require **explicit human approval** before execution.
3. Every action must be **tamper-evident** — logged with hash chaining, verifiable by background job.
4. All financial data comes from **Plaid Sandbox** — no mocked data.
5. This is a **production-ready build** — auth, error handling, tests, and deployment are part of done.

---

## License

MIT
