// Bare UI Template — Static HTML & CSS Layout Only
// Plug in your own state management and fetch calls here!

export default function AccountsDashboard() {
  // Static mock data for visual layout preview
  const accounts = [
    { id: 1, name: "Plaid Checking", type: "Plaid Gold Account", balance: "$110,000.00" },
    { id: 2, name: "Plaid Savings", type: "Plaid High Yield", balance: "$14,580.00" }
  ];

  const transactions = [
    { id: 1, date: "Nov 26, 2024", merchant: "Github Enterprise", category: "Software", status: "Completed", amount: "-$450.00", isNegative: true },
    { id: 2, date: "Nov 28, 2024", merchant: "Plaid Sync Transfer", category: "Transfer", status: "Completed", amount: "+$2,500.00", isNegative: false },
    { id: 3, date: "Nov 30, 2024", merchant: "Stripe Merchant Settlement", category: "Income", status: "Completed", amount: "+$8,400.00", isNegative: false },
    { id: 4, date: "Dec 05, 2024", merchant: "AWS Cloud Hosting", category: "Infrastructure", status: "Pending", amount: "-$1,240.00", isNegative: true }
  ];

  return (
    <div>
      <div className="header-row" style={{ marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Plan, prioritize, and monitor financial autopilot actions with ease.</p>
        </div>
        <div className="action-group">
          <button className="btn-pill-secondary">
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
          <div className="metric-value">$124,580.00</div>
          <div className="metric-sub">
            <span className="trend-badge">↑ 12.4%</span>
            <span>Increased from last month</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Connected Accounts</span>
            <div className="arrow-circle">↗</div>
          </div>
          <div className="metric-value">4</div>
          <div className="metric-sub">
            <span style={{ color: "var(--green-text)", fontWeight: "600" }}>Plaid Synced</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Pending Approvals</span>
            <div className="arrow-circle">↗</div>
          </div>
          <div className="metric-value">2</div>
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
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{tx.date}</td>
                  <td style={{ fontWeight: "600" }}>{tx.merchant}</td>
                  <td>
                    <span className="pill-status status-info">{tx.category}</span>
                  </td>
                  <td>
                    <span className={`pill-status ${tx.status === "Completed" ? "status-completed" : "status-pending"}`}>
                      {tx.status}
                    </span>
                  </td>
                  <td style={{ textAlign: "right", fontWeight: "700", color: tx.isNegative ? "var(--rose-text)" : "var(--green-text)" }}>
                    {tx.amount}
                  </td>
                </tr>
              ))}
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
            <div className="dark-widget-clock">01:24:08</div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.75rem", color: "rgba(255,255,255,0.85)" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#10b981" }}></span>
              <span>Streaming Agent Activity</span>
            </div>
          </div>

          <div className="bento-card" style={{ flexGrow: 1 }}>
            <div className="bento-header" style={{ marginBottom: "12px" }}>
              <h2 className="bento-title" style={{ fontSize: "0.95rem" }}>Connected Institutions</h2>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {accounts.map((acc) => (
                <div key={acc.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 12px", backgroundColor: "var(--bg-card-subtle)", borderRadius: "10px", border: "1px solid var(--border-light)" }}>
                  <div>
                    <div style={{ fontWeight: "700", fontSize: "0.85rem" }}>{acc.name}</div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{acc.type}</div>
                  </div>
                  <div style={{ fontWeight: "700", fontSize: "0.88rem", fontFamily: "var(--font-display)" }}>
                    {acc.balance}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
