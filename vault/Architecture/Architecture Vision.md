# Architecture Vision

> An agent that can view real financial data (via Plaid Sandbox) and propose
> or execute actions — categorize transactions, flag anomalies, move money
> between accounts, pay a bill — through tool calls. A wrong tool call has a
> real consequence, even in sandbox. That constraint drives every decision below.

## Hard Constraints

1. Any tool call that changes state must be **safe to retry** — idempotent. → [[Idempotency]]
2. Actions above a risk threshold require **explicit human approval**. → [[Human-in-the-Loop]]
3. Every action must be traceable and **tamper-evident**. → [[Hash Chaining]], [[Tamper Detection]]
4. Connect to a real financial data sandbox (Plaid Sandbox) — no mocked data. → [[Plaid Sandbox]]
5. Production-ready build — auth, error handling, tests, deployment are part of done.

## Navigation
- [[Tech Stack]]
- [[Decisions Log]]
- [[Roadmap]]
