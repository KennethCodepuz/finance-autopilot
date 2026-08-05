# Approvals Service

**Layer:** Services  
**File:** `backend/app/services/approvals_service.py`

## Functions

- `propose_action_to_agent()`
- `fetch_pending_approvals()`
- `approve_proposal_action()`
- `reject_proposal_action()`

## Depends On

- [[Approvals]]
- [[Database]]
- [[Redis]]
- [[Agent Service]]
- [[Audit Service]]

## Related Concepts

- [[Human-in-the-Loop]]
- [[Outbox Pattern]]
