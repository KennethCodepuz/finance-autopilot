# Decisions Log

**Related:** [[Architecture Vision]], [[Tech Stack]]

## Idempotency Strategy

**Choice:** UUID + DB unique constraint  
**Related concepts:** [[Idempotency]]  

## Approval Workflow

**Choice:** ARQ + Redis job queue  
**Related concepts:** [[ARQ Worker]], [[Human-in-the-Loop]]  

## Audit Trail Integrity

**Choice:** Append-only + Hash chaining + periodic ARQ verification  
**Related concepts:** [[Hash Chaining]], [[Tamper Detection]]  

## Execution Boundary

**Choice:** Internal ledger (Outbox pattern)  
**Related concepts:** [[Outbox Pattern]]  

## Risk Classification

**Choice:** Deterministic scoring rubric  
**Related concepts:** [[Risk Scoring]]  

## Credential Handling

**Choice:** .env (local) + platform env vars (production)  

## Audit Verification Schedule

**Choice:** Hourly incremental + daily full scan (2 AM)  
**Related concepts:** [[ARQ Worker]], [[Hash Chaining]]
