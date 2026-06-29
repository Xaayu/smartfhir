import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";

const COLORS = {
  bg: "#0F1117",
  surface: "#1A1D27",
  border: "#2A2D3E",
  accent: "#4F8EF7",
  success: "#34D399",
  warning: "#FBBF24",
  error: "#F87171",
  muted: "#6B7280",
  text: "#E2E8F0",
  textDim: "#94A3B8",
};

function Stat({ label, value }) {
  return (
    <div style={{
      background: COLORS.surface,
      border: `1px solid ${COLORS.border}`,
      borderRadius: 8,
      padding: 18,
    }}>
      <div style={{
        color: COLORS.muted,
        fontSize: 11,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        marginBottom: 10,
      }}>{label}</div>
      <div style={{ color: COLORS.text, fontSize: 28, fontWeight: 800 }}>{value}</div>
    </div>
  );
}

export default function AdminPage() {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [adminToken, setAdminToken] = useState(localStorage.getItem("smartfhirAdminToken") || "");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [feedback, setFeedback] = useState(null);

  function formatDate(value) {
    if (!value) return "Unknown";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  async function loadMetrics() {
    setLoading(true);
    setError("");

    try {
      const headers = adminToken ? { "X-Admin-Token": adminToken } : {};
      const res = await fetch(`${API_BASE}/admin/metrics`, { headers });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Could not load admin metrics.");
        setLoading(false);
        return;
      }

      localStorage.setItem("smartfhirAdminToken", adminToken);
      setMetrics(data);
      await loadFeedback();
    } catch (e) {
      setError(`Cannot connect to the MedTechTools API at ${API_BASE}.`);
    } finally {
      setLoading(false);
    }
  }

  async function loadFeedback() {
    const headers = adminToken ? { "X-Admin-Token": adminToken } : {};
    const res = await fetch(`${API_BASE}/admin/feedback`, { headers });
    const data = await res.json();

    if (!res.ok) {
      setError(data.detail || "Could not load feedback.");
      return;
    }

    setFeedback(data);
  }

  async function deleteUser(email) {
    if (!window.confirm(`Are you sure you want to delete user ${email}? This will also delete their API key.`)) {
      return;
    }

    setDeleting(email);
    setError("");

    try {
      const headers = adminToken ? { "X-Admin-Token": adminToken } : {};
      const res = await fetch(`${API_BASE}/admin/delete-user`, {
        method: "DELETE",
        headers: {
          ...headers,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Could not delete user.");
        setDeleting(null);
        return;
      }

      // Refresh metrics after successful deletion
      await loadMetrics();
    } catch (e) {
      console.error("Delete user error:", e);
      setError(`Cannot connect to the MedTechTools API: ${e.message}`);
    } finally {
      setDeleting(null);
    }
  }

  useEffect(() => {
    loadMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main style={{
      minHeight: "100vh",
      background: COLORS.bg,
      color: COLORS.text,
      fontFamily: "'Inter', system-ui, sans-serif",
      padding: 32,
    }}>
      <div style={{ maxWidth: 1160, margin: "0 auto" }}>
        <header style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", marginBottom: 28 }}>
          <div>
            <button onClick={() => navigate("/dashboard")} style={{
              background: "none",
              border: 0,
              color: COLORS.accent,
              cursor: "pointer",
              padding: 0,
              marginBottom: 12,
              fontWeight: 700,
            }}>Back to dashboard</button>
            <h1 style={{ fontSize: 32, margin: 0 }}>Founder Analytics</h1>
            <div style={{ color: COLORS.textDim, marginTop: 8 }}>
              V1 signal dashboard for API adoption, endpoint demand, and usage quality.
            </div>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={adminToken}
              onChange={e => setAdminToken(e.target.value)}
              placeholder="Admin token"
              style={{
                background: COLORS.surface,
                border: `1px solid ${COLORS.border}`,
                color: COLORS.text,
                borderRadius: 8,
                padding: "10px 12px",
                minWidth: 220,
              }}
            />
            <button onClick={loadMetrics} disabled={loading} style={{
              background: COLORS.accent,
              border: 0,
              color: "#fff",
              borderRadius: 8,
              padding: "10px 14px",
              fontWeight: 800,
              cursor: loading ? "wait" : "pointer",
            }}>{loading ? "Loading..." : "Refresh"}</button>
          </div>
        </header>

        {error && (
          <div style={{
            background: "#2b0b0b",
            border: "1px solid #F8717144",
            color: "#FCA5A5",
            borderRadius: 8,
            padding: 14,
            marginBottom: 18,
          }}>{error}</div>
        )}

        {metrics && (
          <>
            <section style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: 14,
              marginBottom: 18,
            }}>
              <Stat label="Registered Users" value={metrics.total_users} />
              <Stat label="API Keys" value={metrics.total_api_keys} />
              <Stat label="Total Calls" value={metrics.total_calls} />
              <Stat label="Calls Today" value={metrics.calls_today} />
              <Stat label="Calls 7D" value={metrics.calls_7d} />
              <Stat label="Active Users 7D" value={metrics.active_users_7d} />
              <Stat label="Error Rate" value={`${metrics.error_rate}%`} />
              <Stat label="Avg Response" value={`${metrics.avg_response_time_ms}ms`} />
            </section>

            <section style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 0.9fr) minmax(0, 1.1fr)",
              gap: 18,
            }}>
              <div style={{
                background: COLORS.surface,
                border: `1px solid ${COLORS.border}`,
                borderRadius: 8,
                padding: 18,
              }}>
                <h2 style={{ fontSize: 18, margin: "0 0 16px" }}>Endpoint Usage</h2>
                {(metrics.endpoint_usage || []).length === 0 && (
                  <div style={{ color: COLORS.muted }}>No API calls logged yet.</div>
                )}
                {(metrics.endpoint_usage || []).map(row => (
                  <div key={row.endpoint} style={{
                    display: "flex",
                    justifyContent: "space-between",
                    borderBottom: `1px solid ${COLORS.border}`,
                    padding: "10px 0",
                    gap: 12,
                  }}>
                    <span style={{ color: COLORS.accent, fontFamily: "monospace" }}>{row.endpoint}</span>
                    <strong>{row.calls}</strong>
                  </div>
                ))}
              </div>

              <div style={{
                background: COLORS.surface,
                border: `1px solid ${COLORS.border}`,
                borderRadius: 8,
                padding: 18,
                overflowX: "auto",
              }}>
                <h2 style={{ fontSize: 18, margin: "0 0 16px" }}>Top Users</h2>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                  <thead>
                    <tr style={{ color: COLORS.muted, textAlign: "left" }}>
                      <th style={{ padding: "8px 0" }}>Email</th>
                      <th>Calls</th>
                      <th>Limit</th>
                      <th>Last Used</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(metrics.top_users || []).map(row => (
                      <tr key={row.email} style={{ borderTop: `1px solid ${COLORS.border}` }}>
                        <td style={{ padding: "10px 12px 10px 0", color: COLORS.text }}>{row.email}</td>
                        <td>{row.calls_used}</td>
                        <td>{row.monthly_limit}</td>
                        <td style={{ color: COLORS.textDim }}>{row.last_used_at || "Never"}</td>
                        <td style={{ padding: "10px 0 10px 12px" }}>
                          <button
                            onClick={() => deleteUser(row.email)}
                            disabled={deleting === row.email}
                            style={{
                              background: deleting === row.email ? COLORS.border : "#2b0b0b",
                              border: `1px solid ${COLORS.error}`,
                              color: COLORS.error,
                              borderRadius: 6,
                              padding: "6px 12px",
                              fontSize: 12,
                              fontWeight: 600,
                              cursor: deleting === row.email ? "wait" : "pointer",
                              transition: "all 0.2s",
                            }}
                          >
                            {deleting === row.email ? "Deleting..." : "Delete"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section style={{
              background: COLORS.surface,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 8,
              padding: 18,
              marginTop: 18,
            }}>
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 16,
                alignItems: "flex-start",
                marginBottom: 18,
              }}>
                <div>
                  <h2 style={{ fontSize: 18, margin: "0 0 8px" }}>User Feedback</h2>
                  <div style={{ color: COLORS.textDim, fontSize: 13 }}>
                    Feedback submitted from the landing page widget.
                  </div>
                </div>
                <button onClick={loadFeedback} style={{
                  background: "transparent",
                  border: `1px solid ${COLORS.border}`,
                  color: COLORS.text,
                  borderRadius: 8,
                  padding: "8px 12px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}>Refresh feedback</button>
              </div>

              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: 12,
                marginBottom: 18,
              }}>
                <Stat label="Feedback Items" value={feedback?.total ?? 0} />
                <Stat label="With Email" value={feedback?.with_email ?? 0} />
                <div style={{
                  background: COLORS.bg,
                  border: `1px solid ${COLORS.border}`,
                  borderRadius: 8,
                  padding: 18,
                }}>
                  <div style={{
                    color: COLORS.muted,
                    fontSize: 11,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    marginBottom: 10,
                  }}>Top Feature Votes</div>
                  {(feedback?.feature_counts || []).length === 0 ? (
                    <div style={{ color: COLORS.muted, fontSize: 14 }}>No votes yet.</div>
                  ) : (
                    (feedback?.feature_counts || []).slice(0, 4).map(item => (
                      <div key={item.feature} style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 12,
                        color: COLORS.textDim,
                        fontSize: 13,
                        padding: "4px 0",
                      }}>
                        <span>{item.feature}</span>
                        <strong style={{ color: COLORS.text }}>{item.count}</strong>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {(feedback?.items || []).length === 0 ? (
                <div style={{ color: COLORS.muted }}>No feedback submitted yet.</div>
              ) : (
                <div style={{ display: "grid", gap: 12 }}>
                  {(feedback?.items || []).map(item => (
                    <article key={item.id} style={{
                      background: COLORS.bg,
                      border: `1px solid ${COLORS.border}`,
                      borderRadius: 8,
                      padding: 16,
                    }}>
                      <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 12,
                        alignItems: "flex-start",
                        marginBottom: 12,
                      }}>
                        <div>
                          <div style={{ color: COLORS.text, fontWeight: 800 }}>
                            {item.email || "Anonymous user"}
                          </div>
                          <div style={{ color: COLORS.muted, fontSize: 12, marginTop: 4 }}>
                            {formatDate(item.submitted_at)}
                          </div>
                        </div>
                        <div style={{ color: COLORS.muted, fontFamily: "monospace", fontSize: 11 }}>
                          {item.id}
                        </div>
                      </div>

                      <div style={{
                        color: item.feedback ? COLORS.text : COLORS.muted,
                        fontSize: 14,
                        lineHeight: 1.6,
                        whiteSpace: "pre-wrap",
                        marginBottom: 12,
                      }}>
                        {item.feedback || "No written feedback. Roadmap votes only."}
                      </div>

                      {(item.next_features || []).length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
                          {item.next_features.map(feature => (
                            <span key={feature} style={{
                              border: `1px solid ${COLORS.accent}55`,
                              background: `${COLORS.accent}18`,
                              color: COLORS.accent,
                              borderRadius: 999,
                              padding: "4px 10px",
                              fontSize: 12,
                              fontWeight: 700,
                            }}>{feature}</span>
                          ))}
                        </div>
                      )}

                      <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                        gap: 8,
                        color: COLORS.muted,
                        fontSize: 12,
                      }}>
                        <div><strong style={{ color: COLORS.textDim }}>Page:</strong> {item.page || "Unknown"}</div>
                        <div><strong style={{ color: COLORS.textDim }}>IP:</strong> {item.ip || "Unknown"}</div>
                        <div><strong style={{ color: COLORS.textDim }}>User agent:</strong> {item.user_agent || "Unknown"}</div>
                      </div>
                    </article>
                  ))}
                </div>
              )}

              <div style={{ color: COLORS.muted, fontSize: 12, marginTop: 14 }}>
                Feedback storage: {feedback?.storage || "store/feedback.json"}
              </div>
            </section>

            <div style={{ color: COLORS.muted, fontSize: 12, marginTop: 18 }}>
              Storage: {metrics.storage}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
