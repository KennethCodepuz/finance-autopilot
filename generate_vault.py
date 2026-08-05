"""
generate_vault.py — Finance Autopilot → Obsidian Knowledge Graph

Parses the backend codebase using Python's ast module and generates
interconnected Obsidian markdown notes (wikilinks) covering:
  - Architecture decisions and phases
  - Python modules (services, models, routes, workers, repositories)
  - Concepts (hash chaining, outbox pattern, risk scoring, idempotency)

Run from the project root:
    python generate_vault.py
"""

import ast
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent
BACKEND_APP  = PROJECT_ROOT / "backend" / "app"
VAULT_DIR    = PROJECT_ROOT / "vault"

LAYERS = {
    "services":     "Services",
    "models":       "Models",
    "routes":       "Routes",
    "workers":      "Workers",
    "repositories": "Repositories",
    "schemas":      "Schemas",
    "core":         "Core",
}


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

@dataclass
class ModuleInfo:
    name: str
    layer: str
    path: Path
    classes: list   = field(default_factory=list)
    functions: list = field(default_factory=list)
    imports: list   = field(default_factory=list)


def parse_module(path: Path, layer: str) -> ModuleInfo:
    source = path.read_text(encoding="utf-8")
    tree   = ast.parse(source)
    info   = ModuleInfo(name=path.stem, layer=layer, path=path)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            info.classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info.functions.append(node.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("app."):
                parts = module.split(".")
                if len(parts) >= 2:
                    info.imports.append(parts[-1])

    info.imports = list(dict.fromkeys(
        imp for imp in info.imports if imp != info.name
    ))
    return info


def collect_modules():
    modules = []
    for folder, layer in LAYERS.items():
        layer_path = BACKEND_APP / folder
        if not layer_path.exists():
            continue
        for py_file in layer_path.glob("*.py"):
            if py_file.stem.startswith("__"):
                continue
            modules.append(parse_module(py_file, layer))
    return modules


# ---------------------------------------------------------------------------
# Note generators
# ---------------------------------------------------------------------------

def slug(name):
    return name.replace("_", " ").title()


def wikilink(name):
    return f"[[{slug(name)}]]"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def module_note(info, all_modules):
    lines = [f"# {slug(info.name)}", ""]
    lines += [f"**Layer:** {info.layer}  "]
    lines += [f"**File:** `backend/app/{info.layer.lower()}/{info.name}.py`", ""]

    if info.classes:
        lines += ["## Classes", ""]
        for cls in info.classes:
            lines.append(f"- `{cls}`")
        lines.append("")

    if info.functions:
        lines += ["## Functions", ""]
        for fn in info.functions:
            lines.append(f"- `{fn}()`")
        lines.append("")

    known_names = {m.name for m in all_modules}
    linked = [imp for imp in info.imports if imp in known_names]
    if linked:
        lines += ["## Depends On", ""]
        for imp in linked:
            lines.append(f"- {wikilink(imp)}")
        lines.append("")

    callers = [
        m for m in all_modules
        if info.name in m.imports and m.name != info.name
    ]
    if callers:
        lines += ["## Used By", ""]
        for caller in callers:
            lines.append(f"- {wikilink(caller.name)}")
        lines.append("")

    concept_map = {
        "audit":       ["[[Hash Chaining]]", "[[Tamper Detection]]"],
        "risk":        ["[[Risk Scoring]]"],
        "agent":       ["[[Outbox Pattern]]", "[[Risk Scoring]]"],
        "approvals":   ["[[Human-in-the-Loop]]", "[[Outbox Pattern]]"],
        "task":        ["[[ARQ Worker]]", "[[Outbox Pattern]]"],
        "idempotency": ["[[Idempotency]]"],
        "plaid":       ["[[Plaid Sandbox]]"],
    }
    tags = []
    for keyword, concepts in concept_map.items():
        if keyword in info.name:
            tags.extend(concepts)
    if tags:
        lines += ["## Related Concepts", ""]
        for tag in tags:
            lines.append(f"- {tag}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Concept notes
# ---------------------------------------------------------------------------

CONCEPTS = {
    "Hash Chaining": """
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
""",

    "Outbox Pattern": """
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
""",

    "Risk Scoring": """
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
""",

    "Idempotency": """
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
""",

    "Human-in-the-Loop": """
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
""",

    "ARQ Worker": """
# ARQ Worker

**Related modules:** [[Task]], [[Workers Main]]

## What it is
ARQ is an async job queue backed by Redis. Workers are started separately
from FastAPI and process jobs from the queue.

## Worker functions
| Function | Trigger | Purpose |
|----------|---------|---------|
| `execute_ledger_entry` | Enqueued by `propose_action` | Executes confirmed actions |
| `verify_audit_chain_incremental` | Cron: every hour at :00 | Verifies new audit rows since checkpoint |
| `verify_audit_chain_full` | Cron: daily at 02:00 | Full chain scan from Row 1 |

## WorkerSettings
Defined in `app/workers/main.py`:
- `max_jobs = 1` — audit jobs must not run concurrently
- `job_timeout = 300` — 5 minute ceiling per execution

## Start the worker
```bash
arq app.workers.main.WorkerSettings
```
""",

    "Plaid Sandbox": """
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
""",

    "Tamper Detection": """
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
""",
}


# ---------------------------------------------------------------------------
# Architecture notes
# ---------------------------------------------------------------------------

DECISIONS = [
    ("Idempotency Strategy",         "UUID + DB unique constraint",                              "[[Idempotency]]"),
    ("Approval Workflow",             "ARQ + Redis job queue",                                    "[[ARQ Worker]], [[Human-in-the-Loop]]"),
    ("Audit Trail Integrity",         "Append-only + Hash chaining + periodic ARQ verification", "[[Hash Chaining]], [[Tamper Detection]]"),
    ("Execution Boundary",            "Internal ledger (Outbox pattern)",                        "[[Outbox Pattern]]"),
    ("Risk Classification",           "Deterministic scoring rubric",                            "[[Risk Scoring]]"),
    ("Credential Handling",           ".env (local) + platform env vars (production)",           ""),
    ("Audit Verification Schedule",   "Hourly incremental + daily full scan (2 AM)",             "[[ARQ Worker]], [[Hash Chaining]]"),
]

TECH_STACK = [
    ("Frontend",          "Next.js (App Router, TypeScript)"),
    ("Financial data",    "Plaid Sandbox"),
    ("Backend",           "Python + FastAPI"),
    ("Database",          "PostgreSQL + SQLAlchemy (async)"),
    ("Queue / Jobs",      "ARQ + Redis"),
    ("Containerisation",  "Docker"),
    ("Deployment",        "Render"),
    ("Idempotency",       "UUID + DB unique constraint"),
    ("Audit storage",     "Append-only table + Hash chaining + ARQ verification job"),
    ("Execution boundary","Internal ledger (Outbox pattern)"),
]

PHASES = [
    ("Phase 1", "Foundation & Scaffold",                    "done"),
    ("Phase 2", "Core Data Models & Migration System",      "done"),
    ("Phase 3", "Plaid Sandbox Integration",                "done"),
    ("Phase 4", "Risk Evaluator & Human-in-the-Loop Queue", "done"),
    ("Phase 5", "Tamper-Evident Audit Trail System",        "done"),
    ("Phase 6", "Next.js Dashboard UI & WebSocket Live Feed","pending"),
    ("Phase 7", "LLM Agent Integration & Tool Calling",     "pending"),
    ("Phase 8", "Testing, Security, Polish & Deployment",   "pending"),
]


def decisions_note():
    lines = ["# Decisions Log", "", "**Related:** [[Architecture Vision]], [[Tech Stack]]", ""]
    for decision, choice, related in DECISIONS:
        lines += [f"## {decision}", "", f"**Choice:** {choice}  "]
        if related:
            lines += [f"**Related concepts:** {related}  "]
        lines.append("")
    return "\n".join(lines)


def tech_stack_note():
    lines = ["# Tech Stack", "", "**Related:** [[Architecture Vision]], [[Decisions Log]]", ""]
    lines += ["| Layer | Choice |", "|-------|--------|"]
    for layer, choice in TECH_STACK:
        lines.append(f"| {layer} | {choice} |")
    return "\n".join(lines)


def roadmap_note():
    lines = ["# Roadmap", ""]
    for phase, title, status in PHASES:
        icon = "✅" if status == "done" else "⏳"
        lines.append(f"- {icon} **{phase}** — {title}")
    lines += ["", "**Related:** [[Architecture Vision]], [[Decisions Log]]"]
    return "\n".join(lines)


def vision_note():
    return """# Architecture Vision

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
"""


def index_note(modules):
    lines = ["# Finance Autopilot — Knowledge Graph", ""]
    lines += ["## Architecture", ""]
    lines += [
        "- [[Architecture Vision]]",
        "- [[Tech Stack]]",
        "- [[Decisions Log]]",
        "- [[Roadmap]]",
        "",
    ]
    lines += ["## Concepts", ""]
    for concept in CONCEPTS:
        lines.append(f"- [[{concept}]]")
    lines.append("")

    lines += ["## Modules", ""]
    by_layer = {}
    for m in modules:
        by_layer.setdefault(m.layer, []).append(m)

    for layer in LAYERS.values():
        if layer not in by_layer:
            continue
        lines += [f"### {layer}", ""]
        for m in sorted(by_layer[layer], key=lambda x: x.name):
            lines.append(f"- {wikilink(m.name)}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if VAULT_DIR.exists():
        shutil.rmtree(VAULT_DIR)
    VAULT_DIR.mkdir()

    modules = collect_modules()
    print(f"Found {len(modules)} Python modules")

    write(VAULT_DIR / "Home.md",                         index_note(modules))
    write(VAULT_DIR / "Architecture" / "Architecture Vision.md", vision_note())
    write(VAULT_DIR / "Architecture" / "Tech Stack.md",          tech_stack_note())
    write(VAULT_DIR / "Architecture" / "Decisions Log.md",       decisions_note())
    write(VAULT_DIR / "Architecture" / "Roadmap.md",             roadmap_note())

    for name, content in CONCEPTS.items():
        write(VAULT_DIR / "Concepts" / f"{name}.md", content)

    for info in modules:
        layer_dir = VAULT_DIR / "Modules" / info.layer
        write(layer_dir / f"{slug(info.name)}.md", module_note(info, modules))

    print(f"\nVault generated at: {VAULT_DIR}")
    print("\nNext steps:")
    print("  1. Open Obsidian")
    print("  2. Click 'Open folder as vault'")
    print(f"  3. Select: {VAULT_DIR}")
    print("  4. Press Ctrl+G to open Graph View")


if __name__ == "__main__":
    main()
