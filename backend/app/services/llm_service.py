from datetime import datetime, timezone
import json
import logging
from typing import Any, Optional

from arq import ArqRedis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.agent import AgentPromptResponse, ToolCallResult
from app.services.agent_service import propose_action
from app.services.audit_service import create_and_verify_audit_log

logger = logging.getLogger(__name__)

# OpenAI Tool definitions schema
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "categorize_transaction",
            "description": "Categorize a specific transaction into a budget or expense category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "The ID of the transaction to categorize.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category name (e.g. Dining, Utilities, Transfer, Rent, Subscriptions).",
                    },
                },
                "required": ["transaction_id", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Propose or execute a money transfer to a payee from a bank account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Transfer amount in USD.",
                    },
                    "payee": {
                        "type": "string",
                        "description": "Recipient name or target account name.",
                    },
                    "account_id": {
                        "type": "integer",
                        "description": "Source account ID.",
                    },
                },
                "required": ["amount", "payee", "account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_anomaly",
            "description": "Flag a suspicious transaction as an anomaly for human review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "ID of the transaction to flag.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for flagging as an anomaly.",
                    },
                },
                "required": ["transaction_id", "reason"],
            },
        },
    },
]

async def categorize_transaction(
    transaction_id: int,
    category: str,
    session: AsyncSession,
    redis: ArqRedis,
) -> ToolCallResult:
    """Tool function: Updates transaction category in DB, writes audit log, and streams WS event."""
    result = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
    transactions = result.scalars().first()
    if not transactions:
        return ToolCallResult(
            tool_name="categorize_transaction",
            arguments={"transaction_id": transaction_id, "category": category},
            status="error",
            message=f"Transaction with ID {transaction_id} not found.",
        )

    old_category = transactions.category
    transactions.category = category
    await session.flush()

    audit_payload = {
        "transaction_id": transactions.id,
        "old_category": old_category,
        "new_category": category,
    }
    await create_and_verify_audit_log(
        session=session,
        audit_payload=audit_payload,
        target_id=transactions.id,
        target_type="transaction",
        actor_id="agent_llm",
        action="transaction.categorized",
        actor_type="agent",
    )

    event_data = {
        "event_type": "transaction.categorized",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": audit_payload,
    }
    await redis.publish("activity_feed", json.dumps(event_data))

    return ToolCallResult(
        tool_name="categorize_transaction",
        arguments={"transaction_id": transaction_id, "category": category},
        status="executed",
        message=f"Updated transaction #{transactions.id} category to '{category}'.",
    )


async def transfer_funds(
    amount: float,
    payee: str,
    account_id: int,
    session: AsyncSession,
    redis: ArqRedis,
) -> ToolCallResult:
    """Tool function: Proposes a fund transfer through risk scoring, outbox ledger, and ARQ/HITL queue."""
    ledger_entry = await propose_action(
        action_type="transfer",
        amount=amount,
        payee=payee,
        account_id=account_id,
        session=session,
        redis=redis,
    )

    msg = (
        f"Transfer proposal of ${amount:.2f} to '{payee}' created with "
        f"risk tier '{ledger_entry.risk_tier}' (Score: {ledger_entry.risk_score})."
    )
    return ToolCallResult(
        tool_name="transfer_funds",
        arguments={"amount": amount, "payee": payee, "account_id": account_id},
        status="proposed",
        message=msg,
        ledger_id=ledger_entry.id,
        risk_tier=ledger_entry.risk_tier,
    )


async def flag_anomaly(
    transaction_id: int,
    reason: str,
    session: AsyncSession,
    redis: ArqRedis,
) -> ToolCallResult:
    """Tool function: Flags transaction anomaly and creates outbox ledger entry for human review."""
    result = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
    transactions = result.scalars().first()

    ledger_entry = await propose_action(
        action_type="flag_anomaly",
        amount=float(transactions.amount) if transactions else 0.0,
        payee=transactions.merchant_name if transactions and transactions.merchant_name else (transactions.name if transactions else "Unknown"),
        account_id=transactions.account_id if transactions else 1,
        session=session,
        redis=redis,
    )

    return ToolCallResult(
        tool_name="flag_anomaly",
        arguments={"transaction_id": transaction_id, "reason": reason},
        status="proposed",
        message=f"Flagged transaction #{transaction_id} as anomaly. Reason: {reason}.",
        ledger_id=ledger_entry.id,
        risk_tier=ledger_entry.risk_tier,
    )

async def execute_agent_tool(
    name: str,
    args: dict[str, Any],
    session: AsyncSession,
    redis: ArqRedis,
) -> ToolCallResult:
    """Dispatches tool call requested by LLM to its corresponding Python function handler."""
    if name == "categorize_transaction":
        return await categorize_transaction(
            transaction_id=args.get("transaction_id"),
            category=args.get("category", "General"),
            session=session,
            redis=redis,
        )
    elif name == "transfer_funds":
        return await transfer_funds(
            amount=float(args.get("amount", 0)),
            payee=str(args.get("payee", "Unknown Payee")),
            account_id=int(args.get("account_id", 1)),
            session=session,
            redis=redis,
        )
    elif name == "flag_anomaly":
        return await flag_anomaly(
            transaction_id=args.get("transaction_id"),
            reason=args.get("reason", "Flagged suspicious activity"),
            session=session,
            redis=redis,
        )
    else:
        return ToolCallResult(
            tool_name=name,
            arguments=args,
            status="error",
            message=f"Unknown tool '{name}'.",
        )

async def run_agent_prompt(
    prompt: str,
    session: AsyncSession,
    redis: ArqRedis,
    account_id_filter: Optional[int] = None,
) -> AgentPromptResponse:
    """Runs natural language prompts through LLM function calling or structured fallback."""
    acc_stmt = select(Account)
    if account_id_filter:
        acc_stmt = acc_stmt.where(Account.id == account_id_filter)
    acc_res = await session.execute(acc_stmt)
    accounts = acc_res.scalars().all()

    transactions_stmt = select(Transaction).order_by(Transaction.date.desc()).limit(15)
    transactions_res = await session.execute(transactions_stmt)
    transactions = transactions_res.scalars().all()

    context_str = (
        f"Accounts: {[{'id': a.id, 'name': a.name, 'balance': float(a.balance_current or 0)} for a in accounts]}\n"
        f"Recent Transactions: {[{'id': t.id, 'name': t.name, 'amount': float(t.amount), 'category': t.category} for t in transactions]}"
    )

    tools_called: list[ToolCallResult] = []
    agent_thought = ""

    if settings.openai_api_key and settings.openai_api_key != "sk-placeholder" and not settings.openai_api_key.startswith("your-"):
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Finance Autopilot, an intelligent personal finance AI agent. "
                        "You have access to tool calls to categorize transactions, propose fund transfers, and flag anomalies. "
                        f"Financial Context:\n{context_str}"
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=AGENT_TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message
            agent_thought = msg.content or "Analyzing request and executing required tools."

            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    await redis.publish(
                        "activity_feed",
                        json.dumps({
                            "event_type": "agent.thought",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": {"thought": f"Invoking tool {tool_name} with args {tool_args}"},
                        }),
                    )

                    res = await execute_agent_tool(
                        name=tool_name,
                        args=tool_args,
                        session=session,
                        redis=redis,
                    )
                    tools_called.append(res)

        except Exception as e:
            logger.warning("OpenAI API call failed or unavailable, falling back to rule parser: %s", e)
            agent_thought, tools_called = await _fallback_rule_parser(prompt, accounts, transactions, session, redis)
    else:
        agent_thought, tools_called = await _fallback_rule_parser(prompt, accounts, transactions, session, redis)

    summary = (
        f"Processed prompt. Executed {len(tools_called)} tool action(s)."
        if tools_called
        else f"Processed prompt without invoking tool calls."
    )

    return AgentPromptResponse(
        prompt=prompt,
        agent_thought=agent_thought,
        tools_called=tools_called,
        summary=summary,
    )


async def _fallback_rule_parser(
    prompt: str,
    accounts: list[Account],
    transactions: list[Transaction],
    session: AsyncSession,
    redis: ArqRedis,
) -> tuple[str, list[ToolCallResult]]:
    """Heuristic tool dispatcher for testing or offline mode."""
    lower_p = prompt.lower()
    tools_called: list[ToolCallResult] = []
    default_acc_id = accounts[0].id if accounts else 1

    if "transfer" in lower_p or "move" in lower_p or "pay" in lower_p:
        import re

        amounts = re.findall(r"\$?(\d+(?:\.\d{1,2})?)", prompt)
        amount = float(amounts[0]) if amounts else 150.0
        payee = "Savings Account" if "savings" in lower_p else "External Recipient"

        res = await execute_agent_tool(
            name="transfer_funds",
            args={"amount": amount, "payee": payee, "account_id": default_acc_id},
            session=session,
            redis=redis,
        )
        tools_called.append(res)
        thought = f"Detected transfer request of ${amount} to '{payee}'."

    elif "categorize" in lower_p:
        if transactions:
            transactions = transactions[0]
            cat = "Dining" if "dining" in lower_p or "food" in lower_p else "Utilities"
            res = await execute_agent_tool(
                name="categorize_transaction",
                args={"transaction_id": transactions.id, "category": cat},
                session=session,
                redis=redis,
            )
            tools_called.append(res)
            thought = f"Categorizing transaction #{transactions.id} as {cat}."
        else:
            thought = "No transactions found to categorize."

    elif "flag" in lower_p or "anomaly" in lower_p or "suspicious" in lower_p:
        transactions_id = transactions[0].id if transactions else 1
        res = await execute_agent_tool(
            name="flag_anomaly",
            args={"transaction_id": transactions_id, "reason": "Unusual transaction pattern"},
            session=session,
            redis=redis,
        )
        tools_called.append(res)
        thought = f"Flagged transaction #{transactions_id} as an anomaly."
    else:
        thought = "Analyzed prompt. No actionable financial operation detected."

    return thought, tools_called
