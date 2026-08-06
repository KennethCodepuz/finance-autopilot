// Bare UI Template — Pending Approvals Static Layout

export default function ApprovalsPage() {
  // Static mock queue for layout preview
  const pendingQueue = [
    {
      id: 1,
      action_type: "transfer_funds",
      risk_score: 85,
      amount: "$12,500.00",
      payee: "Acme Logistics LLC",
      account_id: "ACC-9042",
      proposed_at: "Nov 30, 2024 • 14:22:05"
    },
    {
      id: 2,
      action_type: "wire_payment",
      risk_score: 92,
      amount: "$45,000.00",
      payee: "Global Supplier Corp",
      account_id: "ACC-8119",
      proposed_at: "Dec 02, 2024 • 09:15:30"
    }
  ];

  return (
    <div>
      <div className="header-row" style={{ marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Pending Approvals</h1>
          <p className="page-subtitle">Human-in-the-loop queue. Autopilot actions exceeding risk limits are queued here.</p>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {pendingQueue.map((item) => (
          <div key={item.id} className="bento-card" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "24px", alignItems: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span className="pill-status status-rejected">
                  Risk Score: {item.risk_score}
                </span>
                <span className="pill-status status-info" style={{ textTransform: "capitalize" }}>
                  {item.action_type}
                </span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                  Proposed: {item.proposed_at}
                </span>
              </div>
              
              <div style={{ fontSize: "1.25rem", fontWeight: "700", color: "var(--text-main)", fontFamily: "var(--font-display)" }}>
                Transfer <span style={{ color: "var(--green-primary)" }}>{item.amount}</span> to <span>{item.payee}</span>
              </div>

              <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                Account Reference: <span style={{ color: "var(--text-main)", fontWeight: "600" }}>{item.account_id}</span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button className="btn-pill-secondary" style={{ minWidth: "90px", justifyContent: "center", color: "var(--rose-text)", borderColor: "var(--rose-border)" }}>
                Reject
              </button>
              <button className="btn-pill-primary" style={{ minWidth: "90px", justifyContent: "center" }}>
                Approve
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
