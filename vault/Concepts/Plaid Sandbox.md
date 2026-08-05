# Plaid Sandbox

**Related modules:** [[Plaid Service]], [[Plaid]]

## What it is
Plaid Sandbox provides synthetic financial data — accounts, balances,
and transactions — without touching real money.

## Endpoints
| Route | Purpose |
|-------|---------|
| `POST /api/plaid/create-link-token` | Creates a link token for Plaid Link UI |
| `POST /api/plaid/exchange-token` | Exchanges public token for access token |
| `GET /api/plaid/accounts` | Fetches sandbox account balances |
| `GET /api/plaid/transactions` | Fetches sandbox transactions |

## Constraint
> Connect to a real financial data sandbox (Plaid Sandbox) — no mocked data.
> — [[Architecture Vision]]
