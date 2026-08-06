// Bare UI Template — Cryptographic Audit Trail Static Layout

export default function AuditPage() {
  // Static mock audit logs for layout preview
  const auditLogs = [
    {
      id: 104,
      sequence_number: 104,
      timestamp: "Nov 30, 2024 • 14:22:05",
      actor_type: "agent",
      actor_id: "agent_autopilot_v1",
      action: "proposal.created",
      target: "proposal (12)",
      is_verified: true,
      current_hash: "a3f8901c2b4d9e7f8a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f",
      prev_hash: "7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a"
    },
    {
      id: 103,
      sequence_number: 103,
      timestamp: "Nov 28, 2024 • 11:04:12",
      actor_type: "human",
      actor_id: "ken@finance.app",
      action: "proposal_approved",
      target: "proposal (11)",
      is_verified: true,
      current_hash: "7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
      prev_hash: "1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c"
    }
  ];

  return (
    <div>
      <div className="header-row" style={{ marginBottom: "24px" }}>
        <div>
          <h1 className="page-title">Cryptographic Audit Trail</h1>
          <p className="page-subtitle">Append-only log verifying system integrity via SHA-256 chain links.</p>
        </div>
      </div>

      <div className="bento-card" style={{ marginBottom: "20px", display: "flex", gap: "12px", padding: "12px 20px", alignItems: "center" }}>
        <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.05em" }}>Filters:</span>
        
        <select style={{ background: "var(--bg-card-subtle)", border: "1px solid var(--border-light)", borderRadius: "8px", color: "var(--text-main)", padding: "6px 12px", fontSize: "0.82rem", outline: "none", cursor: "pointer" }}>
          <option value="">All Actors</option>
          <option value="agent">Agent Only</option>
          <option value="human">Human Only</option>
        </select>

        <select style={{ background: "var(--bg-card-subtle)", border: "1px solid var(--border-light)", borderRadius: "8px", color: "var(--text-main)", padding: "6px 12px", fontSize: "0.82rem", outline: "none", cursor: "pointer" }}>
          <option value="">All Actions</option>
          <option value="proposal.created">Proposal Created</option>
          <option value="proposal_approved">Proposal Approved</option>
        </select>
      </div>

      <div className="bento-card" style={{ padding: "0" }}>
        <div style={{ overflowX: "auto" }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: "70px", paddingLeft: "20px" }}>Seq</th>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target</th>
                <th>Integrity</th>
                <th style={{ width: "90px", paddingRight: "20px", textAlign: "right" }}>Inspect</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id}>
                  <td style={{ paddingLeft: "20px", color: "var(--text-subtle)", fontWeight: "600" }}>
                    #{log.sequence_number}
                  </td>
                  <td style={{ color: "var(--text-muted)" }}>{log.timestamp}</td>
                  <td>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontWeight: "600", color: "var(--text-main)" }}>{log.actor_id}</span>
                      <span style={{ fontSize: "0.7rem", color: "var(--text-subtle)", textTransform: "uppercase" }}>{log.actor_type}</span>
                    </div>
                  </td>
                  <td>
                    <span className="pill-status status-info">{log.action}</span>
                  </td>
                  <td style={{ color: "var(--text-muted)" }}>{log.target}</td>
                  <td>
                    <span className="pill-status status-completed">Verified</span>
                  </td>
                  <td style={{ paddingRight: "20px", textAlign: "right", color: "var(--green-primary)", fontSize: "0.82rem", fontWeight: "700" }}>
                    Inspect
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 20px", borderTop: "1px solid var(--border-light)" }}>
          <button className="btn-pill-secondary" style={{ padding: "6px 14px", fontSize: "0.8rem" }}>Previous</button>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", alignSelf: "center" }}>Showing Logs 1 - 10</span>
          <button className="btn-pill-secondary" style={{ padding: "6px 14px", fontSize: "0.8rem" }}>Next</button>
        </div>
      </div>
    </div>
  );
}
