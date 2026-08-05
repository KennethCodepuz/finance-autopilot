# Idempotency

**Related modules:** [[Agent Service]], [[Task]]

## What it is
Two idempotency boundaries:
1. **Frontend to Backend** — UUID per request, stored in `IdempotencyKey` table
2. **Backend to Plaid** — same UUID forwarded to Plaid's idempotency header

A duplicate request with the same UUID returns the cached result silently.

## Why UUID + DB constraint
> Fingerprinting breaks on legitimate same-amount transfers.
> Redis adds unjustified infra at this scale.
> UUID + DB constraint is simplest to reason about.
> — [[Decisions Log]]

## TTL
Idempotency keys expire after 1 hour. Frontend warns the user on expiry.
