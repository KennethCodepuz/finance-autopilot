# Outbox Pattern

**Related modules:** [[Agent Service]], [[Task]], [[Approvals Service]]

## What it is
The database is always written **first** as `pending`.
A separate ARQ worker reads pending records and calls Plaid.
Plaid's response transitions the record to `confirmed` or `failed`.

## Why we chose it
> Crash recovery is clean — re-process any stuck `pending` records.
> Idempotency keys protect against Plaid double-execution on retry.
> — [[Decisions Log]]

## State machine
```
pending → processing → confirmed
                    ↘ failed
```

## Key components
- `OutboxLedger` model — stores the ledger entry
- `propose_action()` — writes the `pending` record
- `execute_ledger_entry()` — ARQ worker that processes the record
- `IdempotencyKey` — prevents double execution
