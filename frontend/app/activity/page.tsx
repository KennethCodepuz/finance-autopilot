// Bare UI Template — Real-Time WebSocket Activity Feed Static Layout

export default function ActivityPage() {
  // Static mock events for layout preview
  const mockEvents = [
    {
      id: 1,
      event_type: "proposal.created",
      label: "Proposal Created",
      badgeClass: "status-info",
      time: "14:22:05",
      description: "Autopilot proposed $12,500.00 to Acme Logistics LLC (Ledger #12)"
    },
    {
      id: 2,
      event_type: "proposal.approved",
      label: "Proposal Approved",
      badgeClass: "status-completed",
      time: "14:25:10",
      description: "Human approved ledger proposal #12 of $12,500.00 to Acme Logistics LLC"
    },
    {
      id: 3,
      event_type: "ledger.confirmed",
      label: "Ledger Confirmed",
      badgeClass: "status-completed",
      time: "14:25:12",
      description: "Ledger entry #12 executed successfully in Sandbox."
    }
  ];

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
        {mockEvents.map((evt) => (
          <div key={evt.id} className="bento-card" style={{ display: "flex", gap: "16px", padding: "16px 20px" }}>
            <div style={{ width: "36px", height: "36px", borderRadius: "10px", backgroundColor: "var(--green-light)", color: "var(--green-text)", display: "flex", flexShrink: 0, alignItems: "center", justifyContent: "center" }}>
              <svg style={{ width: "18px", height: "18px" }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            </div>
            <div style={{ flexGrow: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <span className={`pill-status ${evt.badgeClass}`}>{evt.label}</span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-subtle)", fontFamily: "var(--font-display)" }}>{evt.time}</span>
              </div>
              <div style={{ marginTop: "4px", fontSize: "0.92rem", color: "var(--text-main)", fontWeight: "500" }}>
                {evt.description}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
