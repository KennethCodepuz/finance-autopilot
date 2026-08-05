# Human-in-the-Loop

**Related modules:** [[Approvals Service]], [[Risk Service]]

## What it is
High-risk actions (score > 9) are not auto-executed.
They sit in a pending approval queue until a human approves or rejects them.

## Flow
1. Agent proposes action → `propose_action()`
2. Risk scorer returns `high` tier
3. Ledger entry written as `pending`, Redis enqueue is **skipped**
4. Human sees the action in the Pending Approvals screen
5. Human approves → `approve_proposal_action()` → enqueues to ARQ
6. Human rejects → `reject_proposal_action()` → marks as `rejected`

## Audit trail
Every approval and rejection is recorded in [[Audit Service]] with:
- `actor_type = "human"`, `actor_id = "human"`
- `action = "proposal_approved"` or `"proposal_rejected"`
