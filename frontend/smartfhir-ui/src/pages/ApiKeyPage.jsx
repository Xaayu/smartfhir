import { useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { API_BASE } from "../config";

const THEMES = {
  dark: {
    bg: "#0F1117", surface: "#1A1D27", border: "#2A2D3E",
    accent: "#4F8EF7", accentDim: "#1E3A6E",
    success: "#34D399", warning: "#FBBF24", error: "#F87171",
    muted: "#6B7280", text: "#E2E8F0", textDim: "#94A3B8",
    shadow: "rgba(0,0,0,0.35)",
  },
  light: {
    bg: "#F8FAFC", surface: "#FFFFFF", border: "#E2E8F0",
    accent: "#3B82F6", accentDim: "#DBEAFE",
    success: "#10B981", warning: "#F59E0B", error: "#EF4444",
    muted: "#64748B", text: "#1E293B", textDim: "#64748B",
    shadow: "rgba(0,0,0,0.08)",
  },
};

function getApiHeaders() {
  const apiKey = localStorage.getItem("smartfhirApiKey");
  return {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  };
}

const TOOL_LABELS = {
  fhir: "FHIR Resources",
  hl7: "HL7 Suite",
  terminology: "Terminology Center",
};
const benefits = [
  ["Instant API Key", "Start testing the API as soon as you submit your email."],
  ["500 Free API Calls", "Enough room to validate real workflows before paying."],
  ["FHIR Validation", "Catch resource errors with developer-friendly responses."],
  ["Auto Fix", "Normalize common date, gender, status, and enum mistakes."],
  ["Mapping", "Convert messy field names into clean FHIR fields."],
  ["Bundle Generation", "Coming soon for multi-resource workflows."],
  ["No Credit Card Required", "V1 is built for fast product validation."],
];

function ThemeIcon({ theme }) {
  if (theme === "dark") {
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
    );
  }
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  );
}

function StatCard({ label, value, color, colors }) {
  return (
    <div style={{
      background: colors.surface, border: `1px solid ${colors.border}`,
      borderRadius: 12, padding: "18px 20px", flex: 1, minWidth: 120,
      boxShadow: `0 2px 8px ${colors.shadow}`,
    }}>
      <div style={{ color: colors.textDim, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>{label}</div>
      <div style={{ color: color || colors.text, fontSize: 28, fontWeight: 800, lineHeight: 1 }}>{value}</div>
    </div>
  );
}

function UsageBar({ used, limit, colors }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const barColor = pct >= 90 ? colors.error : pct >= 70 ? colors.warning : colors.success;
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ color: colors.textDim, fontSize: 12 }}>Usage this month</span>
        <span style={{ color: barColor, fontSize: 12, fontWeight: 700 }}>{pct}%</span>
      </div>
      <div style={{ height: 8, borderRadius: 99, background: colors.border, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, borderRadius: 99, background: barColor, transition: "width 0.6s ease" }} />
      </div>
      <div style={{ color: colors.muted, fontSize: 11, marginTop: 4 }}>
        {used.toLocaleString()} / {limit.toLocaleString()} calls used
      </div>
    </div>
  );
}

function HeaderButtons({ colors, theme, toggleTheme, onNavigate, onLogout, showLogout }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <button onClick={toggleTheme} aria-label="Toggle Theme" style={{
        width: 34, height: 34, borderRadius: 10, border: `1px solid ${colors.border}`,
        display: "grid", placeItems: "center", background: "transparent", color: colors.text,
        cursor: "pointer", transition: "all 0.2s",
      }}>
        <ThemeIcon theme={theme} />
      </button>
      <button
        onClick={() => onNavigate(-1)}
        style={{
          border: `1px solid ${colors.border}`, background: "transparent", color: colors.text,
          borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600,
          cursor: "pointer", transition: "all 0.2s",
        }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(128,128,128,0.1)"}
        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
      >
        ← Back
      </button>
      <button
        onClick={() => onNavigate("/tools")}
        style={{
          border: `1px solid ${colors.border}`, background: "transparent", color: colors.text,
          borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600,
          cursor: "pointer", transition: "all 0.2s",
        }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(128,128,128,0.1)"}
        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
      >
        Back to tools
      </button>
      {showLogout && (
        <button
          onClick={onLogout}
          style={{
            border: "1px solid #ef4444", background: "transparent", color: "#ef4444",
            borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600,
            cursor: "pointer", transition: "all 0.2s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "rgba(239,68,68,0.1)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          Logout
        </button>
      )}
    </div>
  );
}

function KeyManagerDashboard({ colors, theme, toggleTheme, onLogout, navigate }) {
  const apiKey = localStorage.getItem("smartfhirApiKey") || "";
  const email = localStorage.getItem("smartfhirEmail") || "";
  const [usage, setUsage] = useState(null);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [usageError, setUsageError] = useState("");
  const [keyVisible, setKeyVisible] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchUsage = useCallback(async () => {
    if (!apiKey) return;
    setLoadingUsage(true);
    setUsageError("");
    try {
      const res = await fetch(`${API_BASE}/usage`, { headers: getApiHeaders() });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to fetch usage.");
      setUsage(await res.json());
    } catch (e) {
      setUsageError(e.message);
    } finally {
      setLoadingUsage(false);
    }
  }, [apiKey]);

  function copyKey() {
    navigator.clipboard.writeText(apiKey).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }

  const maskedKey = apiKey
    ? `${apiKey.slice(0, 14)}${"*".repeat(16)}${apiKey.slice(-4)}`
    : "";

  return (
    <div style={{ minHeight: "100vh", background: colors.bg, color: colors.text, fontFamily: "'Inter', system-ui, sans-serif" }}>
      <header style={{
        position: "sticky", top: 0, zIndex: 100,
        background: colors.surface, borderBottom: `1px solid ${colors.border}`,
        padding: "14px 24px", display: "flex", alignItems: "center",
        justifyContent: "space-between", gap: 12,
        boxShadow: `0 2px 8px ${colors.shadow}`,
      }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 17 }}>API Key Manager</div>
          <div style={{ color: colors.textDim, fontSize: 12, marginTop: 2 }}>Manage your API access and monitor usage.</div>
        </div>
        <HeaderButtons colors={colors} theme={theme} toggleTheme={toggleTheme} onNavigate={navigate} onLogout={onLogout} showLogout={true} />
      </header>

      <main style={{ maxWidth: 860, margin: "0 auto", padding: "32px 16px 64px" }}>
        {/* Account card */}
        <div style={{
          background: colors.surface, border: `1px solid ${colors.border}`,
          borderRadius: 16, padding: 20, marginBottom: 20,
          boxShadow: `0 2px 12px ${colors.shadow}`,
        }}>
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>Account</div>
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16, flexWrap: "wrap" }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: "linear-gradient(135deg, #4F8EF7, #00D4AA)",
              display: "grid", placeItems: "center", color: "#fff", fontSize: 22, fontWeight: 800,
            }}>
              {email ? email[0].toUpperCase() : "?"}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{email || "—"}</div>
              <div style={{
                display: "inline-flex", alignItems: "center", gap: 5, marginTop: 3,
                background: colors.success + "22", border: `1px solid ${colors.success}44`,
                color: colors.success, borderRadius: 6, padding: "2px 8px", fontSize: 11, fontWeight: 700,
              }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: colors.success }} />
                Free Plan
              </div>
            </div>
          </div>

          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>Your API Key</div>
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            background: colors.bg, border: `1px solid ${colors.border}`,
            borderRadius: 10, padding: "10px 14px",
          }}>
            <code style={{
              flex: 1, fontFamily: "ui-monospace, monospace", fontSize: 13,
              color: colors.textDim, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>
              {keyVisible ? apiKey : maskedKey}
            </code>
            <button onClick={() => setKeyVisible(v => !v)} style={{
              background: "transparent", border: `1px solid ${colors.border}`,
              color: colors.muted, borderRadius: 6, padding: "4px 8px",
              fontSize: 11, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap",
            }}>
              {keyVisible ? "Hide" : "Show"}
            </button>
            <button onClick={copyKey} style={{
              background: copied ? colors.success : colors.accent,
              border: "none", color: "#fff", borderRadius: 6,
              padding: "6px 14px", fontSize: 12, fontWeight: 700,
              cursor: "pointer", whiteSpace: "nowrap", minWidth: 64, transition: "all 0.2s",
            }}>
              {copied ? "Copied" : "Copy"}
            </button>
          </div>

          <div style={{
            marginTop: 12, background: colors.bg, border: `1px solid ${colors.border}`,
            borderRadius: 8, padding: "10px 14px",
            fontFamily: "ui-monospace, monospace", fontSize: 12, color: colors.muted,
          }}>
            {"curl -H "}
            <span style={{ color: colors.accent }}>{`"X-API-Key: ${maskedKey}"`}</span>
            {" "}
            <span style={{ color: colors.success }}>{`${API_BASE}/validate`}</span>
          </div>
        </div>

        {/* Usage card */}
        <div style={{
          background: colors.surface, border: `1px solid ${colors.border}`,
          borderRadius: 16, padding: 20, marginBottom: 20,
          boxShadow: `0 2px 12px ${colors.shadow}`,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>Usage</div>
            <button onClick={fetchUsage} disabled={loadingUsage} style={{
              background: "transparent", border: `1px solid ${colors.border}`,
              color: colors.textDim, borderRadius: 6, padding: "4px 10px",
              fontSize: 11, fontWeight: 600, cursor: loadingUsage ? "wait" : "pointer",
            }}>
              {loadingUsage ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {usageError && (
            <div style={{
              background: colors.error + "22", border: `1px solid ${colors.error}44`,
              color: colors.error, borderRadius: 8, padding: "10px 14px", fontSize: 13, marginBottom: 16,
            }}>{usageError}</div>
          )}

          {usage ? (
            <>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
                <StatCard label="Calls Used" value={usage.calls_used ?? 0} color={colors.text} colors={colors} />
                <StatCard label="Remaining" value={usage.calls_remaining ?? 0} color={colors.success} colors={colors} />
                <StatCard label="Monthly Limit" value={usage.calls_limit ?? 500} color={colors.accent} colors={colors} />
                <StatCard label="Plan" value={usage.plan ?? "Free"} color={colors.warning} colors={colors} />
              </div>
              <UsageBar used={usage.calls_used ?? 0} limit={usage.calls_limit ?? 500} colors={colors} />
              {usage.last_used && (
                <div style={{ color: colors.muted, fontSize: 12, marginTop: 10 }}>
                  Last used: {new Date(usage.last_used).toLocaleString()}
                </div>
              )}
            </>
          ) : !loadingUsage && (
            <div style={{ color: colors.textDim, fontSize: 13, padding: "20px 0", textAlign: "center" }}>
              No usage data yet. Make your first API call to see stats here.
            </div>
          )}
        </div>

        {/* Quick links */}
        <div style={{
          background: colors.surface, border: `1px solid ${colors.border}`,
          borderRadius: 16, padding: 20,
          boxShadow: `0 2px 12px ${colors.shadow}`,
        }}>
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>Quick Access</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10 }}>
            {[
              { label: "FHIR Resources", icon: "⚡", path: "/tools/fhir" },
              { label: "HL7 Suite", icon: "🔀", path: "/tools/hl7-suite" },
              { label: "Terminology", icon: "🧬", path: "/tools/terminology" },
              { label: "All Tools", icon: "🛠", path: "/tools" },
            ].map(({ label, icon, path }) => (
              <button key={path} onClick={() => navigate(path)} style={{
                background: colors.bg, border: `1px solid ${colors.border}`,
                borderRadius: 10, padding: "12px 16px", cursor: "pointer",
                display: "flex", alignItems: "center", gap: 10,
                color: colors.text, fontSize: 13, fontWeight: 600, textAlign: "left",
                transition: "all 0.2s",
              }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = colors.accent; e.currentTarget.style.background = colors.accentDim; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.background = colors.bg; }}
              >
                <span style={{ fontSize: 18 }}>{icon}</span>
                {label}
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function RegistrationForm({ colors, theme, toggleTheme, navigate, toolLabel, onSuccess }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = email.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      setError("Enter a valid email address.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmed }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Could not create API key."); return; }
      localStorage.setItem("smartfhirEmail", data.email);
      localStorage.setItem("smartfhirApiKey", data.api_key);
      localStorage.setItem("smartfhirPlan", data.plan || "Free");
      localStorage.setItem("smartfhirUsage", String(data.calls_used || 0));
      localStorage.setItem("smartfhirLimit", String(data.calls_limit || 500));
      onSuccess();
    } catch {
      setError(`Cannot connect to the API at ${API_BASE}.`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: colors.bg, color: colors.text, fontFamily: "'Inter', system-ui, sans-serif" }}>
      <style>{`
        @media (max-width: 768px) {
          .registration-body {
            grid-template-columns: 1fr !important;
            gap: 32px !important;
            padding: 32px 16px !important;
          }
          .benefits-grid {
            grid-template-columns: 1fr !important;
          }
          .form-card {
            padding: 24px !important;
          }
        }
      `}</style>
      {/* Header */}
      <header style={{
        position: "sticky", top: 0, zIndex: 100,
        background: colors.surface, borderBottom: `1px solid ${colors.border}`,
        padding: "14px 16px", display: "flex", alignItems: "center",
        justifyContent: "space-between", gap: 12,
        boxShadow: `0 2px 8px ${colors.shadow}`,
      }}>
        <button onClick={() => navigate("/")} style={{
          display: "flex", alignItems: "center", gap: 10,
          background: "none", border: "none", cursor: "pointer", color: colors.text,
        }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8,
            background: "linear-gradient(135deg, #4F8EF7, #00D4AA)",
            display: "grid", placeItems: "center", color: "#fff", fontWeight: 800, fontSize: 14,
          }}>M</div>
          <span style={{ fontWeight: 700, fontSize: 15 }}>MedTechTools</span>
        </button>
        <HeaderButtons colors={colors} theme={theme} toggleTheme={toggleTheme} onNavigate={navigate} showLogout={false} />
      </header>

      {/* Body */}
      <div className="registration-body" style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1.1fr) minmax(300px, 0.9fr)",
        gap: 48, padding: "48px 16px",
        maxWidth: 1200, margin: "0 auto",
      }}>
        <section>
          <div style={{ color: colors.accent, fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 14 }}>Developer preview</div>
          <h1 style={{
            fontFamily: "'Space Grotesk', 'Inter', sans-serif",
            fontSize: "clamp(28px, 5vw, 56px)", lineHeight: 1.05,
            letterSpacing: "-0.03em", margin: "0 0 18px",
          }}>
            {toolLabel ? `Get your key to unlock ${toolLabel}.` : "Get a MedTechTools API key in one step."}
          </h1>
          <p style={{ color: colors.textDim, fontSize: 15, lineHeight: 1.7, maxWidth: 540, marginBottom: 32 }}>
            V1 is intentionally small: one email, one key, and a dashboard for testing validation, mapping, and auto-fix workflows.
          </p>
          <div className="benefits-grid" style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10, maxWidth: 640 }}>
            {benefits.map(([title, desc]) => (
              <div key={title} style={{
                border: `1px solid ${colors.border}`, background: colors.surface,
                borderRadius: 8, padding: 14, display: "flex", gap: 10, alignItems: "flex-start",
              }}>
                <div style={{
                  width: 26, height: 26, borderRadius: 6,
                  background: colors.success + "18", color: colors.success,
                  border: `1px solid ${colors.success}33`,
                  display: "grid", placeItems: "center",
                  fontSize: 12, fontWeight: 800, flexShrink: 0,
                }}>
                  {title === "Bundle Generation" ? ">" : "+"}
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 2 }}>{title}</div>
                  <div style={{ color: colors.muted, fontSize: 12, lineHeight: 1.5 }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section style={{ alignSelf: "center" }}>
          <div className="form-card" style={{
            border: `1px solid ${colors.border}`, background: colors.surface,
            borderRadius: 16, padding: 28, boxShadow: `0 20px 60px ${colors.shadow}`,
          }}>
            <h2 style={{ fontWeight: 800, fontSize: 20, marginBottom: 6 }}>Create your free key</h2>
            <p style={{ color: colors.textDim, fontSize: 13, marginBottom: 20 }}>No password. No trial setup. No credit card.</p>

            <form onSubmit={handleSubmit}>
              <label style={{
                display: "block", color: colors.muted, fontSize: 11, fontWeight: 700,
                letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8,
              }}>Email Address</label>
              <input
                id="email" type="email" placeholder="you@company.com"
                value={email}
                onChange={e => { setEmail(e.target.value); setError(""); }}
                autoComplete="email"
                style={{
                  width: "100%", background: colors.bg, border: `1px solid ${colors.border}`,
                  color: colors.text, borderRadius: 10, padding: "12px 14px",
                  fontSize: 15, outline: "none", marginBottom: 14,
                  transition: "border-color 0.2s", boxSizing: "border-box",
                }}
                onFocus={e => e.currentTarget.style.borderColor = colors.accent}
                onBlur={e => e.currentTarget.style.borderColor = colors.border}
              />
              <button type="submit" disabled={loading} style={{
                width: "100%", background: loading ? colors.accentDim : colors.accent,
                border: "none", color: "#fff", borderRadius: 10,
                padding: "14px 16px", fontSize: 15, fontWeight: 800,
                cursor: loading ? "wait" : "pointer", transition: "all 0.2s",
              }}>
                {loading ? "Creating API key..." : "Create my API key"}
              </button>
            </form>

            {error && (
              <div style={{
                marginTop: 14, background: colors.error + "22",
                border: `1px solid ${colors.error}44`, color: colors.error,
                borderRadius: 8, padding: "10px 14px", fontSize: 13,
              }}>{error}</div>
            )}

            <div style={{
              marginTop: 20, background: colors.bg, border: `1px solid ${colors.border}`,
              borderRadius: 8, padding: "11px 14px",
              fontFamily: "ui-monospace, monospace", color: colors.muted, fontSize: 12, lineHeight: 1.7,
            }}>
              {"curl -H "}
              <span style={{ color: colors.accent }}>"X-API-Key: sk_live_..."</span>
              {" "}
              <span style={{ color: colors.success }}>{`${API_BASE}/validate`}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default function ApiKeyPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestedTool = searchParams.get("tool");
  const toolLabel = TOOL_LABELS[requestedTool];

  const [theme, setTheme] = useState(() => localStorage.getItem("smartfhirTheme") || "dark");
  const colors = THEMES[theme] || THEMES.dark;

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("smartfhirTheme", next);
  }

  const [hasKey, setHasKey] = useState(() => !!localStorage.getItem("smartfhirApiKey"));

  function handleLogout() {
    ["smartfhirApiKey","smartfhirEmail","smartfhirPlan","smartfhirUsage",
     "smartfhirLimit","smartfhirRemaining","smartfhirLastUsed"].forEach(k => localStorage.removeItem(k));
    setHasKey(false);
    navigate("/");
  }

  if (hasKey) {
    return (
      <KeyManagerDashboard
        colors={colors} theme={theme} toggleTheme={toggleTheme}
        onLogout={handleLogout} navigate={navigate}
      />
    );
  }

  return (
    <RegistrationForm
      colors={colors} theme={theme} toggleTheme={toggleTheme}
      navigate={navigate} toolLabel={toolLabel}
      onSuccess={() => setHasKey(true)}
    />
  );
}
