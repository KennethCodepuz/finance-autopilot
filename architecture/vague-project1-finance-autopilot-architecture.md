# architecture.md — Project 1: Personal Finance Autopilot

## Stage 1 — Tool Calling (Consequential Actions)

---

# Vision

An agent that can view real financial data (via a sandbox provider like
Plaid Sandbox) and propose or execute actions — categorize transactions,
flag anomalies, move money between accounts, pay a bill — through tool
calls. Unlike a support ticket, a wrong tool call here has a real
consequence, even in sandbox. That constraint drives every decision below.

---

# Hard Constraints (non-negotiable, regardless of how you design it)

1. Any tool call that changes state must be **safe to retry** — a network
   timeout followed by a retry must never cause the action to happen twice.
2. Actions above a risk threshold require **explicit human approval**
   before execution — the agent cannot self-authorize everything.
3. Every action must be traceable: who/what proposed it, who/what approved
   it, when, and why — and this record must be **tamper-evident**, not
   just loggable.
4. You must connect to a real financial data sandbox, not mocked data.
5. This is a production-ready build, not an MVP — see `tutor.md` for what
   that means in practice (auth, error handling, tests, deployment are all
   part of "done," not follow-up work).

---

# Frontend Requirement

Build a real dashboard, not just Swagger docs. React (you already know
this stack). Required screens:

- **Accounts overview** — balances, recent transactions, pulled live from
  the sandbox connection
- **Pending approvals queue** — every action awaiting human sign-off,
  with approve/deny actions that actually resume the agent's execution
- **Audit trail viewer** — a chronological, filterable view of every
  action taken, by whom/what, with the reasoning attached
- **Agent activity feed** — a live or near-live view of what the agent is
  currently proposing/doing, not just historical logs

The approval queue is the screen that matters most — it's the human-in-
the-loop control surface for the whole system, so it needs to feel
trustworthy to use, not like an afterthought bolted onto an API.

---

# Open Design Questions

You need to resolve each of these before or while building. Don't guess —
research the tradeoffs, make a call, write it down.

### 1. Idempotency
A tool call to "transfer $50" times out on the client side. Did it
actually execute on the server? If you retry, how do you guarantee it
doesn't execute twice?
*Look into: idempotency keys, at-least-once vs. exactly-once delivery
semantics.*

### 2. Approval workflow
Where does a "pending approval" action live between the agent proposing it
and a human deciding? How does the human's decision get back into the
system and resume execution?
*Look into: polling vs. webhooks, state machines, long-running workflow
patterns.*

### 3. Audit trail integrity
What storage pattern prevents even someone with DB access from silently
editing history after the fact?
*Look into: append-only tables, event sourcing, hash chaining.*

### 4. Execution boundary
Should your tools call the sandbox API directly, or go through an internal
ledger/service that tracks pending vs. confirmed state separately from the
external system's state?
*Look into: the saga pattern, two-phase commit, compensating
transactions.*

### 5. Risk classification
Who or what decides an action is "high risk" and needs approval — a fixed
rule set, the LLM's own judgment, or both? What happens when they
disagree?

### 6. Credential handling
How are your sandbox API credentials stored, rotated, and kept out of
logs/code/version control?

---

# What's Deliberately Not Specified

Tech stack, folder structure, and database schema are yours to decide as
part of answering the questions above — they follow from your answers, not
the other way around. Use `tutor.md` to work through each question before
committing to a schema or a stack.

---

# Decisions Log

| Date | Decision Point | Options Considered | Choice | Reasoning |
|------|----------------|---------------------|--------|-----------|
| 2026-07-19 | Idempotency strategy | Client-generated UUID + DB unique constraint / Server-side fingerprinting / Distributed lock (Redis) / At-most-once (no retry) | Option A: Client-generated UUID + DB unique constraint | Two keys needed — one at frontend→backend hop, one at backend→Plaid hop. Fingerprinting breaks on legitimate duplicate transfers. Redis adds infra dependency not justified at this scale. At-most-once gives bad UX for financial actions. UUID + DB constraint is simplest to reason about and sufficient. Server silently replays cached result on duplicate. 1-hour TTL with frontend warning. |
| 2026-07-19 | Approval workflow | DB + Polling / DB + Event trigger / Message queue (BullMQ + Redis) / Workflow engine (Temporal) | Option C: BullMQ + Redis message queue | Clean separation of concerns — queue handles ordering, retries, and worker lifecycle. Denial signals back to agent to propose an alternative; after N denials job is marked dead (Dead Letter Queue) and user is notified via activity feed. Earns Redis as a dependency in a way idempotency did not. Also introduces jobs/workers as a learning goal. |

---

# Current Status

```txt
Open questions resolved: 2 / 6
Currently working on: Question 3 — Audit Trail Integrity
Blocked on:
```
