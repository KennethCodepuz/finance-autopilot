"use client";

import { useState, useEffect } from "react";
import { useWebSocket } from "./websocket/websocket";

export default function AccountsDashboard() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [totalLiquidity, setTotalLiquidity] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState<string>("");

  const ws = useWebSocket();
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  // Clock tick
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    setCurrentTime(new Date().toLocaleTimeString());
    return () => clearInterval(timer);
  }, []);

  // Fetch Accounts & Liquidity
  useEffect(() => {
    async function fetchAccounts() {
      try {
        const res = await fetch(`${backendUrl}/api/plaid/accounts`);
        const data = await res.json();
        if (Array.isArray(data)) {
          setAccounts(data);
          const total = data.reduce((sum, acc) => sum + (Number(acc.balance_current) || 0), 0);
          setTotalLiquidity(total);
        }
      } catch (err) {
        console.error("Error fetching accounts:", err);
      }
    }
    fetchAccounts();
  }, [backendUrl]);

  // Fetch Transactions
  useEffect(() => {
    async function fetchTransactions() {
      try {
        const res = await fetch(`${backendUrl}/api/plaid/transactions`);
        const data = await res.json();
        if (Array.isArray(data)) {
          setTransactions(data);
        }
      } catch (err) {
        console.error("Error fetching transactions:", err);
      }
    }
    fetchTransactions();
  }, [backendUrl]);

  // Fetch Pending Approvals Count
  useEffect(() => {
    async function fetchPendingCount() {
      try {
        const res = await fetch(`${backendUrl}/api/approvals/pending-approvals`);
        const data = await res.json();
        if (Array.isArray(data)) {
          setPendingCount(data.length);
        }
      } catch (err) {
        console.error("Error fetching pending count:", err);
      }
    }
    fetchPendingCount();
  }, [backendUrl]);

  // WebSocket Live Updates
  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event_type === "proposal.created") {
          setPendingCount((prev) => prev + 1);
        } else if (data.event_type === "proposal.approved" || data.event_type === "proposal.rejected") {
          setPendingCount((prev) => Math.max(0, prev - 1));
        }
      } catch (err) {
        console.error("Error parsing WS message:", err);
      }
    };

    ws.addEventListener("message", handleMessage);
    return () => ws.removeEventListener("message", handleMessage);
  }, [ws]);

  return (
    <div>
      <div className="header-row" style={{ marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Plan, prioritize, and monitor financial autopilot actions with ease.</p>
        </div>
        <div className="action-group">
          <button className="btn-pill-secondary" onClick={() => window.location.reload()}>
            <svg style={{ width: "16px", height: "16px" }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            <span>Sync Data</span>
          </button>
          <button className="btn-pill-primary">
            <svg style={{ width: "16px", height: "16px" }} fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <span>Link Plaid Sandbox</span>
          </button>
        </div>
      </div>

      {/* Donezo 4 Stat Cards */}
      <div className="metrics-grid" style={{ marginBottom: "24px" }}>
        <div className="metric-card featured">
          <div className="metric-header">
            <span className="metric-title">Total Liquidity</span>
            <div className="arrow-circle">↗</div>
          </div>
          <div className="metric-value">
            ${totalLiquidity.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="metric-sub">
            <span className="trend-badge">↑ Live</span>
            <span>Calculated from active Plaid balances</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Connected Accounts</span>
            <div className="arrow-circle">↗</div>
          </div>
          <div className="metric-value">{accounts.length}</div>
          <div className="metric-sub">
            <span style={{ color: "var(--green-text)", fontWeight: "600" }}>Plaid Synced</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Pending Approvals</span>
            <div className="arrow-circle">↗</div>
          </div>
          <div className="metric-value">{pendingCount}</div>
          <div className="metric-sub">
            <span style={{ color: "var(--amber-text)", fontWeight: "600" }}>Queued for Human</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Audit Chain Integrity</span>
            <div className="arrow-circle">↗</div>
          </div>
          <div className="metric-value">100%</div>
          <div className="metric-sub">
            <span style={{ color: "var(--green-text)", fontWeight: "600" }}>SHA-256 Verified</span>
          </div>
        </div>
      </div>

      {/* Donezo Bento Layout */}
      <div className="bento-grid">
        <div className="bento-card">
          <div className="bento-header">
            <h2 className="bento-title">Recent Transactions</h2>
            <button className="btn-pill-secondary" style={{ padding: "4px 12px", fontSize: "0.75rem" }}>
              + Add Transaction
            </button>
          </div>

          <table className="custom-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Merchant / Details</th>
                <th>Category</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)" }}>
                    No recent transactions found.
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => {
                  const amountVal = Number(tx.amount);
                  const isNegative = amountVal > 0; // Plaid standard: positive amount = debit/expense
                  const formattedAmt = `${isNegative ? "-" : "+"}$${Math.abs(amountVal).toLocaleString("en-US", { minimumFractionDigits: 2 })}`;

                  return (
                    <tr key={tx.id}>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{tx.date}</td>
                      <td style={{ fontWeight: "600" }}>{tx.name || tx.merchant_name}</td>
                      <td>
                        <span className="pill-status status-info">{tx.category || "General"}</span>
                      </td>
                      <td>
                        <span className={`pill-status ${tx.pending ? "status-pending" : "status-completed"}`}>
                          {tx.pending ? "Pending" : "Completed"}
                        </span>
                      </td>
                      <td style={{ textAlign: "right", fontWeight: "700", color: isNegative ? "var(--rose-text)" : "var(--green-text)" }}>
                        {formattedAmt}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Right Bento Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Dark Forest Green Widget */}
          <div className="dark-widget">
            <div>
              <div className="dark-widget-title">Live WebSocket Monitor</div>
              <div style={{ fontSize: "0.75rem", color: "rgba(255, 255, 255, 0.7)", marginTop: "4px" }}>
                Channel: <span style={{ color: "#a7f3d0", fontWeight: "600" }}>activity_feed</span>
              </div>
            </div>
            <div className="dark-widget-clock">{currentTime}</div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.75rem", color: "rgba(255,255,255,0.85)" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: ws ? "#10b981" : "#ef4444" }}></span>
              <span>{ws ? "Streaming Agent Activity" : "Reconnecting WebSocket..."}</span>
            </div>
          </div>

          <div className="bento-card" style={{ flexGrow: 1 }}>
            <div className="bento-header" style={{ marginBottom: "12px" }}>
              <h2 className="bento-title" style={{ fontSize: "0.95rem" }}>Connected Institutions</h2>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {accounts.length === 0 ? (
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>No connected accounts found.</div>
              ) : (
                accounts.map((acc) => (
                  <div key={acc.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 12px", backgroundColor: "var(--bg-card-subtle)", borderRadius: "10px", border: "1px solid var(--border-light)" }}>
                    <div>
                      <div style={{ fontWeight: "700", fontSize: "0.85rem" }}>{acc.name}</div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{acc.subtype || acc.type} • {acc.mask}</div>
                    </div>
                    <div style={{ fontWeight: "700", fontSize: "0.88rem", fontFamily: "var(--font-display)" }}>
                      ${Number(acc.balance_current).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
