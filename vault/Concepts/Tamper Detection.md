# Tamper Detection

**Related modules:** [[Audit Service]], [[Task]]

## Two-layer verification
1. **Write-time** (`create_and_verify_audit_log`) — verifies the chain before
   writing each new row. Catches bugs in the write path immediately.

2. **Background job** — independently re-verifies stored rows after commit.
   Catches post-hoc direct database tampering.

## What each check detects
| Check | Detects |
|-------|---------|
| `recompute_hash(row) != row.current_hash` | Row data was changed after writing |
| `row.prev_hash != prev_row.current_hash` | Chain link broken (row deleted/reordered) |

## Realistic attack scenarios
- Change `actor_id` column to hide who authorised a transaction
- Change `payload["payload"]["amount"]` to hide transfer amount
- Delete a row — detected by broken chain link on the next row
