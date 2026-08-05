# Hash Chaining

**Related modules:** [[Audit Service]], [[Task]]

## What it is
Each audit log row stores:
- `current_hash` — SHA-256 of this row's full payload
- `prev_hash` — the `current_hash` of the previous row

This forms an unbroken chain. Any edit to a historical row breaks every hash
that follows it, making tampering mathematically detectable.

## Why we chose it
> Append-only prevents accidental edits by convention. Hash chaining makes any
> edit or deletion mathematically detectable — same mechanism as JWT but chained
> across records.
> — [[Decisions Log]]

## Key functions
- `calculate_audit_hash()` — writes a new row with correct hashes
- `recompute_hash()` — verifies a stored row's hash against its columns
- `create_and_verify_audit_log()` — wrapper that verifies the chain before writing

## Verification schedule
- **Hourly** → incremental job (checkpoint-based, Redis)
- **Daily 2 AM** → full table scan from Row 1

## Pitfall: SQLite timezone stripping
SQLite strips timezone info from `DateTime` columns on round-trip.
`recompute_hash` uses `payload["timestamp"]` (the original serialised string)
instead of `timestamp.isoformat()` to avoid hash mismatches in tests.
