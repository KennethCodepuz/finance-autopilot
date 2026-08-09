"use client";

import { useState, useEffect } from "react";
import { useWebSocket } from "../websocket/websocket";

export default function ActivityPage() {
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
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

  const getEventBadgeClass = (eventType: string) => {
    switch (eventType) {
      case "proposal.created":
        return "status-info";
      case "proposal.approved":
      case "proposal_approved":
      case "ledger.confirmed":
      case "ledger_entry.confirmed":
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
          <h1 className="page-title">Agent Activity Feed</h1>
          <p className="page-subtitle">Real-time event log streaming proposals and ledger actions via WebSocket.</p>
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

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {activityFeed.length === 0 ? (
          <div className="bento-card" style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
            Listening for live WebSocket events... Try approving a proposal or creating a proposal to see live events stream in!
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
