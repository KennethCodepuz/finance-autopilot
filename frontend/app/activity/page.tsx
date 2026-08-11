"use client";

import { useState, useEffect } from "react";
import { useWebSocket } from "../websocket/websocket";

export default function ActivityPage() {
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const [promptInput, setPromptInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [agentResponse, setAgentResponse] = useState<any>(null);

  const ws = useWebSocket();
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  // 1. Fetch initial historical logs on mount
  useEffect(() => {
    async function fetchInitialHistory() {
      try {
        const res = await fetch(`${backendUrl}/api/audit/logs?limit=20&offset=0`);
        const data = await res.json();
        if (Array.isArray(data)) {
          const initialEvents = data.map((log: any) => ({
            event_type: log.action || "audit.log",
            timestamp: log.timestamp || log.created_at,
            payload: log.payload || {}
          }));
          setActivityFeed(initialEvents);
        }
      } catch (err) {
        console.error("Error fetching initial activity history:", err);
      }
    }
    fetchInitialHistory();
  }, [backendUrl]);

  // 2. Listen for live incoming WebSocket events
  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const activity = JSON.parse(event.data);
        setActivityFeed((prev) => [activity, ...prev]);
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.addEventListener("message", handleMessage);

    return () => {
      ws.removeEventListener("message", handleMessage);
    };
  }, [ws]);

  const handlePromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptInput.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setAgentResponse(null);

    try {
      const res = await fetch(`${backendUrl}/api/agent/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: promptInput.trim() }),
      });
      const data = await res.json();
      setAgentResponse(data);
      setPromptInput("");
    } catch (err) {
      console.error("Error running agent prompt:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getEventBadgeClass = (eventType: string) => {
    switch (eventType) {
      case "proposal.created":
      case "agent.thought":
        return "status-info";
      case "proposal.approved":
      case "proposal_approved":
      case "ledger.confirmed":
      case "ledger_entry.confirmed":
      case "transaction.categorized":
        return "status-completed";
      case "proposal.rejected":
      case "proposal_rejected":
        return "status-rejected";
      default:
        return "status-pending";
    }
  };

  const getEventDescription = (evt: any) => {
    const payload = evt.payload || {};
    const amount = payload.amount ? `$${payload.amount}` : "";
    const payee = payload.payee || "";
    const action = payload.action_type || evt.event_type || "action";

    switch (evt.event_type) {
      case "agent.thought":
        return `AI Thought: ${payload.thought || "Processing task..."}`;
      case "transaction.categorized":
        return `Categorized transaction #${payload.transaction_id} as '${payload.new_category}'`;
      case "proposal.created":
        return `AI Agent proposed ${action} of ${amount} to ${payee}`;
      case "proposal.approved":
      case "proposal_approved":
        return `Human approved ${action} of ${amount} to ${payee || "payee"}`;
      case "proposal.rejected":
      case "proposal_rejected":
        return `Human rejected ${action} of ${amount} to ${payee || "payee"}`;
      case "ledger.confirmed":
      case "ledger_entry.confirmed":
        return `Background Ledger confirmed ${action} of ${amount} to ${payee || "payee"}`;
      default:
        return `Event '${evt.event_type}' processed for ${payee || "ledger item"}`;
    }
  };

  return (
    <div>
      <div className="header-row" style={{ marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Agent Activity Feed & Command Console</h1>
          <p className="page-subtitle">Interact with the AI agent and stream live real-time proposals, tool calls, and ledger events.</p>
        </div>
        <div>
          <span className="pill-status status-completed" style={{ padding: "6px 14px" }}>
            <span style={{
              display: "inline-block",
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: "var(--green-text)",
              marginRight: "8px"
            }}></span>
            LIVE CHANNELS ACTIVE
          </span>
        </div>
      </div>

      {/* AI Agent Interactive Prompt Console */}
      <div className="bento-card" style={{ padding: "24px", marginBottom: "24px" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "8px", color: "var(--text-main)" }}>
          Instruct Finance Agent
        </h3>
        <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", marginBottom: "16px" }}>
          Type a natural language instruction (e.g. <em>&quot;Move $600 to my savings account for rent&quot;</em> or <em>&quot;Categorize transaction #1 as Dining&quot;</em>).
        </p>

        <form onSubmit={handlePromptSubmit} style={{ display: "flex", gap: "12px" }}>
          <input
            type="text"
            placeholder="What would you like the agent to analyze or do?"
            value={promptInput}
            onChange={(e) => setPromptInput(e.target.value)}
            style={{
              flexGrow: 1,
              padding: "12px 16px",
              borderRadius: "8px",
              border: "1px solid var(--border-color)",
              backgroundColor: "var(--bg-elevated)",
              color: "var(--text-main)",
              fontSize: "0.95rem",
              outline: "none"
            }}
          />
          <button
            type="submit"
            disabled={isSubmitting || !promptInput.trim()}
            style={{
              padding: "12px 24px",
              borderRadius: "8px",
              backgroundColor: isSubmitting ? "var(--border-color)" : "var(--primary-color, #2563eb)",
              color: "#ffffff",
              fontWeight: "600",
              border: "none",
              cursor: isSubmitting ? "not-allowed" : "pointer",
              transition: "background-color 0.2s"
            }}
          >
            {isSubmitting ? "Processing..." : "Run Agent"}
          </button>
        </form>

        {agentResponse && (
          <div style={{ marginTop: "20px", padding: "16px", borderRadius: "8px", backgroundColor: "var(--bg-subtle, #f8fafc)", border: "1px solid var(--border-color)" }}>
            <div style={{ fontWeight: "600", fontSize: "0.92rem", color: "var(--text-main)", marginBottom: "6px" }}>
              Agent Output Summary:
            </div>
            <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", marginBottom: "10px" }}>
              {agentResponse.agent_thought}
            </p>
            {agentResponse.tools_called?.map((tc: any, i: number) => (
              <div key={i} style={{ fontSize: "0.85rem", padding: "8px 12px", borderRadius: "6px", backgroundColor: "var(--bg-elevated)", border: "1px solid var(--border-color)", marginTop: "6px" }}>
                <strong>Tool Invoked:</strong> <code>{tc.tool_name}</code> — {tc.message}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Activity Feed */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {activityFeed.length === 0 ? (
          <div className="bento-card" style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
            Listening for live WebSocket events... Instruct the agent or approve proposals to watch live events stream in!
          </div>
        ) : (
          activityFeed.map((evt, idx) => {
            const timeStr = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
            const badgeClass = getEventBadgeClass(evt.event_type);
            const description = getEventDescription(evt);

            return (
              <div key={idx} className="bento-card" style={{ display: "flex", gap: "16px", padding: "16px 20px" }}>
                <div style={{ width: "36px", height: "36px", borderRadius: "10px", backgroundColor: "var(--green-light)", color: "var(--green-text)", display: "flex", flexShrink: 0, alignItems: "center", justifyContent: "center" }}>
                  <svg style={{ width: "18px", height: "18px" }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                  </svg>
                </div>
                <div style={{ flexGrow: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                    <span className={`pill-status ${badgeClass}`}>{evt.event_type}</span>
                    <span style={{ fontSize: "0.78rem", color: "var(--text-subtle)", fontFamily: "var(--font-display)" }}>{timeStr}</span>
                  </div>
                  <div style={{ marginTop: "4px", fontSize: "0.92rem", color: "var(--text-main)", fontWeight: "500" }}>
                    {description}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
