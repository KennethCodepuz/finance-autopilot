"use client";

import { useState, useEffect } from "react";
import { getPendingApprovals } from "../utils/useFetchApprovals";
import { useWebSocket } from "../websocket/websocket";

export default function ApprovalsPage() {
  const [pendingQueue, setPendingQueue] = useState<any[]>([]);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const ws = useWebSocket();

  useEffect(() => {
    async function getApprovals() {
      try {
        const res = await getPendingApprovals(backendUrl);
        setPendingQueue(Array.isArray(res) ? res : []);
      } catch (err) {
        console.error(err);
      }
    }
    getApprovals();
  }, [backendUrl]);

  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        if (data.event_type === "proposal.created") {
          setPendingQueue((prev) => [data.payload, ...prev]);
        }

        if (data.event_type === "proposal.approved" || data.event_type === "proposal.rejected") {
          setPendingQueue((prev) => prev.filter((item) => (item.id || item.ledger_id) !== data.payload.ledger_id));
        }
      } catch (error) {
        console.error("Error parsing message:", error);
      }
    };

    ws.addEventListener("message", handleMessage);
    return () => {
      ws.removeEventListener("message", handleMessage);
    };
  }, [ws]);

  const proposalAccept = async (id: number | string, event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    try {
      const res = await fetch(`${backendUrl}/api/approvals/approve/${id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (res.ok) {
        setPendingQueue((prev) => prev.filter((item) => (item.id || item.ledger_id) !== id));
      } else {
        const errorData = await res.json().catch(() => ({}));
        console.error("Failed to accept proposal:", errorData);
      }
    } catch (error) {
      console.error("Network error accepting proposal:", error);
    }
  };

  const proposalReject = async (id: number | string, event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    try {
      const res = await fetch(`${backendUrl}/api/approvals/reject/${id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (res.ok) {
        setPendingQueue((prev) => prev.filter((item) => (item.id || item.ledger_id) !== id));
      } else {
        const errorData = await res.json().catch(() => ({}));
        console.error("Failed to reject proposal:", errorData);
      }
    } catch (error) {
      console.error("Network error rejecting proposal:", error);
    }
  };

  return (
    <div>
      <div className="header-row" style={{ marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Pending Approvals</h1>
          <p className="page-subtitle">Human-in-the-loop queue. Autopilot actions exceeding risk limits are queued here.</p>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {pendingQueue.length === 0 ? (
          <div className="bento-card" style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
            🎉 No pending approvals! Autopilot is operational.
          </div>
        ) : (
          pendingQueue.map((item) => {
            const itemId = item.id || item.ledger_id;
            return (
              <div key={itemId} className="bento-card" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "24px", alignItems: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                    <span className="pill-status status-rejected">
                      Risk Score: {item.risk_score}
                    </span>
                    <span className="pill-status status-info" style={{ textTransform: "capitalize" }}>
                      {item.action_type || item.payload?.action_type}
                    </span>
                    <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      Proposed: {item.created_at ? new Date(item.created_at).toLocaleTimeString() : "Just now"}
                    </span>
                  </div>

                  <div style={{ fontSize: "1.25rem", fontWeight: "700", color: "var(--text-main)", fontFamily: "var(--font-display)" }}>
                    Transfer <span style={{ color: "var(--green-primary)" }}>${item.amount || item.payload?.amount}</span> to <span>{item.payee || item.payload?.payee}</span>
                  </div>

                  <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                    Account Reference: <span style={{ color: "var(--text-main)", fontWeight: "600" }}>{item.account_id || item.payload?.account_id || "Checking"}</span>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "10px" }}>
                  <button onClick={(e) => proposalReject(itemId, e)} className="btn-pill-secondary" style={{ minWidth: "90px", justifyContent: "center", color: "var(--rose-text)", borderColor: "var(--rose-border)" }}>
                    Reject
                  </button>
                  <button onClick={(e) => proposalAccept(itemId, e)} className="btn-pill-primary" style={{ minWidth: "90px", justifyContent: "center" }}>
                    Approve
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
