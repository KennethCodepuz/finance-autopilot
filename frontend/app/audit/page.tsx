"use client"
import { useState, useEffect } from "react";

export default function AuditPage() {
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [action, setAction] = useState("");
  const [actor_type, setActorType] = useState("");

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    async function fetchAuditLogs(){

      const params = new URLSearchParams();
      if (action) params.append("action", action);
      if (actor_type) params.append("actor_type", actor_type);
      
      const response = await fetch(`${backendUrl}/api/audit/logs?${params.toString()}`);
      const data = await response.json();
      console.log(data);
      setAuditLogs(data);
    }
    fetchAuditLogs();
    
  }, [action, actor_type]);

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
        
        <select onChange={(e) => setActorType(e.target.value)} style={{ background: "var(--bg-card-subtle)", border: "1px solid var(--border-light)", borderRadius: "8px", color: "var(--text-main)", padding: "6px 12px", fontSize: "0.82rem", outline: "none", cursor: "pointer" }}>
          <option value="">All Actors</option>
          <option value="agent">Agent Only</option>
          <option value="human">Human Only</option>
        </select>

        <select onChange={(e) => setAction(e.target.value)} style={{ background: "var(--bg-card-subtle)", border: "1px solid var(--border-light)", borderRadius: "8px", color: "var(--text-main)", padding: "6px 12px", fontSize: "0.82rem", outline: "none", cursor: "pointer" }}>
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
                  <td style={{ color: "var(--text-muted)" }}>{log.target_type}</td>
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
