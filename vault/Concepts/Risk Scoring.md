# Risk Scoring

**Related modules:** [[Risk Service]], [[Agent Service]]

## Scoring rubric
| Factor | Points |
|--------|--------|
| Amount > $500 | +7 |
| Amount > $2000 | +5 (additive) |
| Action type = transfer | +5 |
| Action type = bill_pay | +3 |
| Payee is new (not in transactions) | +8 |

## Tiers
| Score | Tier | Outcome |
|-------|------|---------|
| <= 9 | Low | Auto-execute via ARQ |
| > 9 | High | Human approval required |

## Why deterministic rules
> Hard rules define a scoring rubric. Deterministic scorer sums points and applies
> tier thresholds. Two logical components (proposer + evaluator) built as separate
> functions so swapping evaluator to an LLM is a one-function change.
> — [[Decisions Log]]
