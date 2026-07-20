# architecture.md — Personal Finance Autopilot

---

## Vision

An agent that can view real financial data (via Plaid Sandbox) and propose
or execute actions — categorize transactions, flag anomalies, move money
between accounts, pay a bill — through tool calls. A wrong tool call has a
real consequence, even in sandbox. That constraint drives every decision below.

---

## Hard Constraints (non-negotiable)

1. Any tool call that changes state must be **safe to retry** — a network
   timeout followed by a retry must never cause the action to happen twice.
2. Actions above a risk threshold require **explicit human approval**
   before execution — the agent cannot self-authorize everything.
3. Every action must be traceable: who/what proposed it, who/what approved
   it, when, and why — and this record must be **tamper-evident**.
4. Connect to a real financial data sandbox (Plaid Sandbox) — no mocked data.
5. Production-ready build — auth, error handling, tests, and deployment are
   part of "done," not follow-up work.

---

## Frontend

React. Required screens:

- **Accounts overview** — balances and recent transactions, pulled live from Plaid Sandbox.
- **Pending approvals queue** — every action awaiting human sign-off, with
  approve/deny that resumes agent execution. This is the most important screen.
- **Audit trail viewer** — chronological, filterable view of every action,
  by whom/what, with reasoning attached.
- **Agent activity feed** — live or near-live view of what the agent is
  currently proposing/doing, including dead-lettered actions and discard notifications.

---

## Tech Stack

| Layer | Choice | Decided |
|-------|--------|---------|
| Frontend | Next.js (App Router, TypeScript) | 2026-07-20 (impl) |
| Financial data | Plaid Sandbox | Day 1 (architecture requirement) |
| Backend | Python + FastAPI | 2026-07-19 (impl) |
| Database | PostgreSQL + SQLAlchemy ORM | 2026-07-19 (impl) |
| Queue / background jobs | ARQ + Redis | 2026-07-19 (Decision 2 + impl) |
| Containerization | Docker | 2026-07-19 (impl) |
| Deployment | Render | 2026-07-19 (impl) |
| Real-time feed | WebSockets | 2026-07-19 (impl) |
| Idempotency | UUID + DB unique constraint | 2026-07-19 (Decision 1) |
| Audit trail storage | Append-only table + Hash chaining + ARQ verification job | 2026-07-19 (Decision 3) |
| Execution boundary | Internal ledger (Outbox pattern) — DB written first, separate process calls Plaid | 2026-07-19 (Decision 4) |
| Risk classification | Deterministic scoring rubric (hard rules → points → tier) with LLM escalation path | 2026-07-19 (Decision 5) |
| Credential handling | `.env` (local) + platform env vars (production) + `.env.example` committed | 2026-07-19 (Decision 6) |

---

## Decisions Log

| Date | Decision Point | Options Considered | Choice | Reasoning |
|------|----------------|---------------------|--------|-----------|
| 2026-07-19 | Idempotency strategy | Client UUID + DB unique constraint / Server-side fingerprinting / Distributed lock (Redis) / At-most-once | **Client UUID + DB unique constraint** | Two keys needed — one at frontend→backend hop, one at backend→Plaid hop. Fingerprinting breaks on legitimate same-amount transfers. Redis adds unjustified infra at this scale. At-most-once gives bad UX. UUID + DB constraint is simplest to reason about. Server silently replays cached result on duplicate. 1-hour TTL with frontend warning. |
| 2026-07-19 | Approval workflow | DB + Polling / DB + Event trigger / ARQ + Redis / Temporal workflow engine | **ARQ + Redis job queue** | Clean separation — queue handles ordering, retries, and worker lifecycle. Denial signals back to agent to propose an alternative. After N denials, job is dead-lettered and user is notified via activity feed. ARQ chosen over BullMQ (Node.js only) and Celery (not natively async) because it is async-native and fits FastAPI naturally. |
| 2026-07-19 | Audit trail integrity | Plain mutable table / Append-only table / Hash chaining / External immutable log / Event sourcing | **Append-only + Hash chaining + periodic ARQ verification job** | Append-only prevents accidental edits by convention. Hash chaining makes any edit or deletion mathematically detectable — same mechanism as JWT but chained across records. Periodic ARQ background job walks the chain and alerts on breakage. |
| 2026-07-19 | Execution boundary | Direct call + local state / Internal ledger (Outbox pattern) / Saga with compensating transactions | **Option B: Internal ledger (Outbox pattern)** | DB is always written first as `pending`. Separate ARQ worker reads pending records and calls Plaid. Plaid’s response transitions the record to `confirmed` or `failed`. Crash recovery is clean — re-process any stuck `pending` records. Idempotency keys (Decision 1) protect against Plaid double-execution on retry. |
| 2026-07-19 | Risk classification | Fixed rules only / LLM judgment only / Scoring rubric + deterministic evaluator / Two-LLM critic pattern | **Deterministic scoring rubric, LLM escalation path wired in** | Hard rules define a scoring rubric (e.g. new payee +8pts, amount >$500 +7pts). Deterministic scorer sums points and applies tier thresholds (1–9 = low risk, auto-execute; 10–20 = high risk, human approval required). Two logical components — proposer and evaluator — built as separate functions so swapping evaluator to an LLM is a one-function change. No middle tier; clean binary outcome. |
| 2026-07-19 | Credential handling | Hardcoded / Committed .env / .env + .gitignore / .env + platform env vars | **.env for local (gitignored) + platform env vars for production** | `.env` keeps secrets out of source code locally. `.gitignore` added on first commit before any secrets are added. `.env.example` committed to document required variable names with no values. Production uses Render dashboard env vars. Raw config objects never logged. |
| 2026-07-19 | Backend framework | Node/Express / FastAPI / Django | **Python + FastAPI** | Async-native, pairs cleanly with ARQ and SQLAlchemy async. Fast to build APIs, strong typing with Pydantic. |
| 2026-07-19 | Database + ORM | PostgreSQL + SQLAlchemy | **PostgreSQL + SQLAlchemy ORM** | PostgreSQL supports append-only patterns and has strong constraint enforcement for idempotency keys. SQLAlchemy is the standard Python ORM with async support. |
| 2026-07-19 | Containerization | Docker | **Docker** | Single `docker-compose.yml` runs FastAPI + PostgreSQL + Redis locally. Matches Render’s deployment model. |
| 2026-07-19 | Deployment | Render | **Render** | Simple deploy from Git, native env var management (no `.env` file on server), supports Docker. |
| 2026-07-20 | Frontend framework | React + Vite / Next.js | **Next.js (App Router, TypeScript)** | App Router supports server components and streaming out of the box. Built-in routing removes react-router-dom. Pairs well with WebSocket client components. pnpm used for package management. |

---

## Project Implementation Roadmap & Phases

- `[x]` **Phase 1: Foundation & Scaffold**
  - Architecture decisions locked & documented
  - Monorepo scaffold: FastAPI backend (`uv`), Next.js frontend (`pnpm`), Docker Compose
  - GitHub repo setup & README documentation

- `[x]` **Phase 2: Core Data Models & Migration System**
  - Database schema design (Accounts, Transactions, Idempotency Keys, Outbox Ledger, Audit Log)
  - SQLAlchemy Async models setup
  - Alembic migrations setup & initial migration execution

- `[ ]` **Phase 3: Plaid Sandbox Integration**
  - Plaid client initialization (Sandbox environment)
  - Link token creation and public token exchange endpoints
  - Fetch & sync sandbox account balances and transaction data

- `[ ]` **Phase 4: Risk Evaluator & Human-in-the-Loop Approval Queue**
  - Deterministic risk scoring rubric (points & tier evaluation)
  - Outbox Pattern execution boundary (`pending` → Plaid execution → `confirmed` / `failed`)
  - ARQ background job worker queue & Dead Letter Queue (DLQ) handling
  - Human approval & rejection API endpoints

- `[ ]` **Phase 5: Tamper-Evident Audit Trail System**
  - Cryptographic hash-chaining logic for audit events (`prev_hash` calculation)
  - ARQ background periodic job for hash-chain integrity verification & alerting

- `[ ]` **Phase 6: Next.js Dashboard UI & WebSocket Live Feed**
  - WebSocket backend router for real-time agent activity streaming
  - **Accounts Overview Screen** (Balances & transactions live sync)
  - **Pending Approvals Screen** (Human approval queue control surface)
  - **Audit Trail Viewer** (Filterable timeline & cryptographic verification status)
  - **Agent Activity Feed** (Live WebSocket stream)

- `[ ]` **Phase 7: LLM Agent Integration & Tool Calling**
  - AI Agent service with tool-calling capabilities (Categorize, Transfer, Flag Anomaly)
  - Integration with Risk Evaluator & Approval Queue

- `[ ]` **Phase 8: Testing, Security, Polish & Deployment**
  - Unit & integration tests (`pytest`)
  - Error handling, production logging, and security verification
  - Render deployment configuration & container build validation

---

## Current Status

```txt
Architecture Open Questions Resolved: 6 / 6
Current Active Phase: Phase 3 — Plaid Sandbox Integration
Next Step: Initialize Plaid client and implement link token & token exchange endpoints.
```
