import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

// ── Design tokens (matches existing dashboard) ────────────
const C = {
  bg:      "#0A0E1A",
  surface: "#1A2035",
  card:    "#141828",
  border:  "#242B42",
  accent:  "#4F8EF7",
  teal:    "#00D4AA",
  error:   "#F87171",
  warning: "#FBBF24",
  success: "#34D399",
  text:    "#E2E8F0",
  dim:     "#94A3B8",
  muted:   "#64748B",
};

// ── Sample data ───────────────────────────────────────────
const SAMPLE_PATIENT = {
  resourceType: "Patient",
  id: "PT-2024-001",
  name: [{ given: ["John"], family: "Doe" }],
  birthDate: "1985-08-15",
  gender: "male",
  telecom: [
    { system: "phone", value: "+1-555-0123" },
    { system: "email", value: "john.doe@hospital.org" }
  ],
  address: [{
    line: ["123 Main Street"],
    city: "Boston",
    state: "MA",
    postalCode: "02101",
    country: "US"
  }],
  note: [{ text: "Call patient at 555-9876 or email backup@gmail.com for follow-up." }]
};

const SAMPLE_BUNDLE = {
  resourceType: "Bundle",
  type: "collection",
  entry: [
    {
      resource: {
        resourceType: "Patient",
        id: "PT-2024-001",
        name: [{ given: ["John"], family: "Doe" }],
        birthDate: "1985-08-15",
        telecom: [{ system: "email", value: "john.doe@hospital.org" }]
      }
    },
    {
      resource: {
        resourceType: "Observation",
        id: "obs-001",
        status: "final",
        subject: { reference: "Patient/PT-2024-001" },
        effectiveDateTime: "2024-01-20",
        note: [{ text: "Patient John Doe called at 555-0199" }]
      }
    }
  ]
};

// ── Tiny helpers ──────────────────────────────────────────
function Badge({ children, color = C.accent }) {
  return (
    <span style={{
      background: color + "22",
      color,
      border: `1px solid ${color}44`,
      borderRadius: 4,
      padding: "2px 8px",
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
    }}>{children}</span>
  );
}

function Tag({ children, color = C.muted }) {
  return (
    <span style={{
      background: color + "18",
      color,
      borderRadius: 100,
      padding: "3px 10px",
      fontSize: 12,
      fontWeight: 500,
      border: `1px solid ${color}30`,
    }}>{children}</span>
  );
}

function JsonBlock({ data, maxHeight = 500 }) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div style={{ position: "relative", height: "100%", display: "flex", flexDirection: "column" }}>
      <button onClick={copy} style={{
        position: "absolute", top: 10, right: 10,
        background: copied ? C.success + "22" : C.surface,
        border: `1px solid ${copied ? C.success : C.border}`,
        color: copied ? C.success : C.muted,
        borderRadius: 6, padding: "4px 10px",
        fontSize: 11, fontWeight: 600, cursor: "pointer",
        fontFamily: "inherit", zIndex: 1,
        transition: "all 0.2s",
      }}>{copied ? "✓ Copied" : "Copy"}</button>
      <pre style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 10,
        padding: "14px 16px",
        fontSize: 12,
        color: C.dim,
        overflowX: "auto",
        overflowY: "auto",
        maxHeight,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        lineHeight: 1.65,
        margin: 0,
        flex: 1,
        minHeight: 200,
        wordBreak: "break-word",
        whiteSpace: "pre-wrap",
      }}>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

function StatPill({ label, value, color = C.text }) {
  return (
    <div style={{
      background: C.card,
      border: `1px solid ${C.border}`,
      borderRadius: 10,
      padding: "12px 14px",
      flex: "1 1 minmax(100px, 1fr)",
      minWidth: "min(100px, 100%)",
      textAlign: "center",
    }}>
      <div style={{ color, fontSize: 20, fontWeight: 700, fontFamily: "'Space Grotesk', sans-serif" }}>
        {value}
      </div>
      <div style={{ color: C.muted, fontSize: 10, marginTop: 3, textTransform: "uppercase", letterSpacing: "0.06em" }}>
        {label}
      </div>
    </div>
  );
}

// ── Mode selector ─────────────────────────────────────────
const MODES = [
  {
    id: "pseudonymize",
    label: "Pseudonymize",
    icon: "🎭",
    desc: "Replace with realistic fake data",
    example: "John Doe → James Wilson",
    color: C.teal,
    recommended: true,
  },
  {
    id: "mask",
    label: "Mask",
    icon: "🔒",
    desc: "Partially hide, keep format",
    example: "John Doe → J*** D**",
    color: C.accent,
    recommended: false,
  },
  {
    id: "redact",
    label: "Redact",
    icon: "🚫",
    desc: "Replace with [REDACTED]",
    example: "John Doe → [REDACTED]",
    color: C.error,
    recommended: false,
  },
];

function ModeCard({ mode, selected, onSelect }) {
  return (
    <div onClick={() => onSelect(mode.id)} style={{
      background: selected ? mode.color + "0F" : C.surface,
      border: `1.5px solid ${selected ? mode.color : C.border}`,
      borderRadius: 12,
      padding: "14px 16px",
      cursor: "pointer",
      flex: "1 1 minmax(200px, 1fr)",
      minWidth: "min(200px, 100%)",
      transition: "all 0.18s",
      position: "relative",
    }}>
      {mode.recommended && (
        <div style={{
          position: "absolute", top: -10, right: 12,
          background: C.teal, color: "#0A0E1A",
          fontSize: 10, fontWeight: 700,
          padding: "2px 10px", borderRadius: 100,
          letterSpacing: "0.05em", textTransform: "uppercase",
        }}>Recommended</div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 18 }}>{mode.icon}</span>
        <span style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontWeight: 700, fontSize: 14,
          color: selected ? mode.color : C.text,
        }}>{mode.label}</span>
      </div>
      <div style={{ fontSize: 12, color: C.dim, marginBottom: 8 }}>{mode.desc}</div>
      <div style={{
        fontFamily: "monospace", fontSize: 11,
        color: C.muted,
        background: C.card,
        borderRadius: 6, padding: "4px 8px",
      }}>{mode.example}</div>
    </div>
  );
}

// ── Audit report panel ────────────────────────────────────
function AuditPanel({ report }) {
  if (!report) return null;

  const phiTypes = report.phi_by_type || {};
  const fields   = report.fields_cleaned || [];

  const typeColors = {
    name:       C.error,
    date:       C.warning,
    email:      C.accent,
    phone:      "#C084FC",
    address:    "#FB923C",
    geographic: "#34D399",
    identifier: C.teal,
    biometric:  C.error,
    contact:    C.accent,
    location:   "#FB923C",
    fax:        "#C084FC",
    ssn:        C.error,
    url:        C.muted,
    ip:         C.muted,
  };

  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 14,
      overflow: "hidden",
      marginTop: 20,
    }}>
      {/* Header */}
      <div style={{
        padding: "14px 16px",
        borderBottom: `1px solid ${C.border}`,
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 8,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 16 }}>📋</span>
          <span style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: 700, fontSize: 14, color: C.text,
          }}>Audit Report</span>
          <Badge color={C.teal}>HIPAA Safe Harbor</Badge>
        </div>
        <span style={{ fontSize: 12, color: C.muted, fontFamily: "monospace" }}>
          {report.timestamp?.slice(0, 19).replace("T", " ")} UTC
        </span>
      </div>

      <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 16 }}>

        {/* Stats row */}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <StatPill label="PHI Found" value={report.phi_items_found} color={C.error} />
          <StatPill label="Fields Cleaned" value={fields.length} color={C.warning} />
          <StatPill
            label="Standard"
            value="Safe Harbor"
            color={C.teal}
          />
        </div>

        {/* PHI by type */}
        {Object.keys(phiTypes).length > 0 && (
          <div>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>
              PHI Categories
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
              {Object.entries(phiTypes).map(([type, count]) => (
                <div key={type} style={{
                  display: "flex", alignItems: "center", gap: 6,
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 8, padding: "5px 12px",
                  fontSize: 12,
                }}>
                  <div style={{
                    width: 7, height: 7, borderRadius: "50%",
                    background: typeColors[type] || C.muted,
                    flexShrink: 0,
                  }} />
                  <span style={{ color: C.dim, textTransform: "capitalize" }}>{type}</span>
                  <span style={{
                    color: typeColors[type] || C.text,
                    fontWeight: 700, fontFamily: "monospace",
                  }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fields cleaned */}
        {fields.length > 0 && (
          <div>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>
              Fields Cleaned
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {fields.map(f => (
                <span key={f} style={{
                  fontFamily: "monospace", fontSize: 11,
                  color: C.accent,
                  background: C.accent + "12",
                  border: `1px solid ${C.accent}30`,
                  borderRadius: 5, padding: "2px 8px",
                }}>{f}</span>
              ))}
            </div>
          </div>
        )}

        {/* HIPAA note */}
        <div style={{
          background: C.teal + "0A",
          border: `1px solid ${C.teal}25`,
          borderRadius: 8, padding: "10px 14px",
          fontSize: 12, color: C.dim, lineHeight: 1.6,
        }}>
          <span style={{ color: C.teal, fontWeight: 600 }}>✓ HIPAA Compliant · </span>
          {report.standard}
        </div>
      </div>
    </div>
  );
}

// ── PHI Scanner (free text) ───────────────────────────────
function TextScanner({ apiKey }) {
  const [text, setText] = useState("");
  const [mode, setMode] = useState("pseudonymize");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function scan() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/phi/scan-text`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
        },
        body: JSON.stringify({ text, mode }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Scan failed");
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <textarea
        value={text}
        onChange={e => { setText(e.target.value); setResult(null); }}
        placeholder="Paste any text to scan for PHI — notes, comments, discharge summaries..."
        style={{
          background: C.card,
          border: `1px solid ${C.border}`,
          borderRadius: 10, padding: "12px 14px",
          color: C.text, fontFamily: "inherit",
          fontSize: 13, lineHeight: 1.7,
          resize: "vertical", outline: "none",
          minHeight: 120,
          transition: "border-color 0.2s",
        }}
        onFocus={e => e.target.style.borderColor = C.accent}
        onBlur={e => e.target.style.borderColor = C.border}
      />

      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <select
          value={mode}
          onChange={e => setMode(e.target.value)}
          style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 8, padding: "8px 12px",
            color: C.text, fontSize: 13, outline: "none",
            fontFamily: "inherit", cursor: "pointer",
            flex: "1 1 minmax(140px, 1fr)",
          }}
        >
          <option value="pseudonymize">Pseudonymize</option>
          <option value="mask">Mask</option>
          <option value="redact">Redact</option>
        </select>

        <button onClick={scan} disabled={loading || !text.trim()} style={{
          background: loading ? C.muted : C.accent,
          color: "#fff", border: "none", borderRadius: 8,
          padding: "9px 20px", fontSize: 13, fontWeight: 600,
          cursor: loading ? "wait" : "pointer",
          fontFamily: "inherit", transition: "all 0.2s",
          flex: "1 1 minmax(120px, 1fr)",
        }}>
          {loading ? "Scanning..." : "Scan for PHI"}
        </button>
      </div>

      {error && (
        <div style={{
          background: C.error + "15", border: `1px solid ${C.error}40`,
          borderRadius: 8, padding: 12,
          color: C.error, fontSize: 13,
        }}>{error}</div>
      )}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", gap: 10 }}>
            <StatPill
              label="PHI Found"
              value={result.phi_found}
              color={result.phi_found > 0 ? C.error : C.success}
            />
            {Object.entries(result.phi_types || {}).map(([type, count]) => (
              <StatPill key={type} label={type} value={count} color={C.warning} />
            ))}
          </div>

          <div className="desktop-text-grid" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12 }}>
            <div>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                Original
              </div>
              <div style={{
                background: C.card, border: `1px solid ${C.error}40`,
                borderRadius: 10, padding: 14,
                fontSize: 13, color: C.dim, lineHeight: 1.7,
                minHeight: 80,
                wordBreak: "break-word",
              }}>{result.original_text}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                Cleaned
              </div>
              <div style={{
                background: C.card, border: `1px solid ${C.teal}40`,
                borderRadius: 10, padding: 14,
                fontSize: 13, color: C.text, lineHeight: 1.7,
                minHeight: 80,
                wordBreak: "break-word",
              }}>{result.cleaned_text}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main component ────────────────────────────────────────
export default function PHIDeidentifier({ apiKey }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("resource");
  const [theme, setTheme] = useState(() => localStorage.getItem("smartfhirTheme") || "dark");

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("smartfhirTheme", newTheme);
  };

  const [mode, setMode] = useState("pseudonymize");
  const [inputJson, setInputJson] = useState(JSON.stringify(SAMPLE_PATIENT, null, 2));
  const [bundleJson, setBundleJson] = useState(JSON.stringify(SAMPLE_BUNDLE, null, 2));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [includeAudit, setIncludeAudit] = useState(true);
  const [jsonError, setJsonError] = useState(null);

  const isBundle = activeTab === "bundle";

  function validateJson(str) {
    try {
      JSON.parse(str);
      setJsonError(null);
      return true;
    } catch (e) {
      setJsonError("Invalid JSON — " + e.message);
      return false;
    }
  }

  async function run() {
    const raw = isBundle ? bundleJson : inputJson;
    if (!validateJson(raw)) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const parsed = JSON.parse(raw);
    const endpoint = isBundle ? "/phi/deidentify-bundle" : "/phi/deidentify";
    const body = isBundle
      ? { bundle: parsed, mode, audit: includeAudit }
      : { resource: parsed, mode, audit: includeAudit };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey || "",
        },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function loadSample() {
    if (isBundle) {
      setBundleJson(JSON.stringify(SAMPLE_BUNDLE, null, 2));
    } else {
      setInputJson(JSON.stringify(SAMPLE_PATIENT, null, 2));
    }
    setResult(null);
    setJsonError(null);
  }

  const deidentifiedData = result?.deidentified_resource || result?.deidentified_bundle;
  const auditReport = result?.audit_report;

  return (
    <div style={{
      background: C.bg,
      minHeight: "100vh",
      fontFamily: "'Inter', system-ui, sans-serif",
      color: C.text,
    }}>

      {/* ── Header ── */}
      <div style={{
        borderBottom: `1px solid ${C.border}`,
        padding: "16px 20px",
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 12,
      }}>
        <div style={{ flex: "1 1 minmax(280px, 1fr)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4, flexWrap: "wrap" }}>
            <span style={{ fontSize: 20 }}>🛡️</span>
            <h1 style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: 18, fontWeight: 700,
              letterSpacing: "-0.02em", margin: 0,
            }}>PHI De-identifier</h1>
            <Badge color={C.teal}>HIPAA Safe Harbor</Badge>
          </div>
          <p style={{ margin: 0, fontSize: 12, color: C.muted, lineHeight: 1.5 }}>
            Remove or replace patient identifiers from FHIR resources before sharing with vendors or for testing.
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={toggleTheme} style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 8, padding: "7px 12px",
            color: C.dim, fontSize: 12, cursor: "pointer",
            fontWeight: 500, transition: "all 0.2s",
            fontFamily: "inherit",
          }}>{theme === "dark" ? "☀️" : "🌙"}</button>
          <button onClick={() => navigate('/api-key')} style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 8, padding: "7px 14px",
            color: C.dim, fontSize: 12, cursor: "pointer",
            fontWeight: 500, transition: "all 0.2s",
            fontFamily: "inherit",
          }}>Manage API</button>
          <button onClick={() => navigate('/tools')} style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 8, padding: "7px 14px",
            color: C.dim, fontSize: 12, cursor: "pointer",
            fontWeight: 500, transition: "all 0.2s",
            fontFamily: "inherit",
          }}>Back to tools</button>
          <button onClick={() => {
            localStorage.removeItem('smartfhir_api_key');
            navigate('/');
          }} style={{
            background: C.error + "15", border: `1px solid ${C.error}40`,
            borderRadius: 8, padding: "7px 14px",
            color: C.error, fontSize: 12, cursor: "pointer",
            fontWeight: 500, transition: "all 0.2s",
            fontFamily: "inherit",
          }}>Logout</button>
        </div>
      </div>

      <div style={{ padding: "20px", maxWidth: 1280, margin: "0 auto" }}>

        {/* ── Mode selector ── */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>
            De-identification Mode
          </div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {MODES.map(m => (
              <ModeCard
                key={m.id}
                mode={m}
                selected={mode === m.id}
                onSelect={setMode}
              />
            ))}
          </div>
        </div>

        {/* ── Input type tabs ── */}
        <div style={{
          display: "flex", gap: 4,
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 10, padding: 4,
          width: "100%", marginBottom: 20,
          overflowX: "auto",
        }}>
          {[
            { id: "resource", label: "Single Resource", icon: "📄" },
            { id: "bundle",   label: "Bundle",          icon: "📦" },
            { id: "text",     label: "Free Text Scan",  icon: "🔍" },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setResult(null); setError(null); }}
              style={{
                background: activeTab === tab.id ? C.accent : "none",
                border: "none",
                borderRadius: 7,
                padding: "8px 14px",
                color: activeTab === tab.id ? "#fff" : C.muted,
                fontSize: 12, fontWeight: activeTab === tab.id ? 600 : 400,
                cursor: "pointer", fontFamily: "inherit",
                transition: "all 0.15s",
                display: "flex", alignItems: "center", gap: 6,
                whiteSpace: "nowrap",
                flex: "1 1 auto",
              }}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── Free text tab ── */}
        {activeTab === "text" && (
          <div style={{
            background: C.surface,
            border: `1px solid ${C.border}`,
            borderRadius: 14, padding: 20,
          }}>
            <TextScanner apiKey={apiKey} />
          </div>
        )}

        {/* ── Resource / Bundle tabs ── */}
        {activeTab !== "text" && (
          <div className="desktop-grid" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 20, alignItems: "start" }}>

            {/* Left — Input */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  {isBundle ? "FHIR Bundle Input" : "FHIR Resource Input"}
                </div>
                <button onClick={loadSample} style={{
                  background: "none", border: `1px solid ${C.border}`,
                  borderRadius: 6, padding: "4px 10px",
                  color: C.muted, fontSize: 11, cursor: "pointer",
                  fontFamily: "inherit",
                }}>Load sample</button>
              </div>

              <textarea
                value={isBundle ? bundleJson : inputJson}
                onChange={e => {
                  isBundle ? setBundleJson(e.target.value) : setInputJson(e.target.value);
                  setResult(null);
                  validateJson(e.target.value);
                }}
                style={{
                  background: C.card,
                  border: `1.5px solid ${jsonError ? C.error : C.border}`,
                  borderRadius: 10, padding: "12px 14px",
                  color: C.text,
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 11, lineHeight: 1.6,
                  resize: "vertical", outline: "none",
                  minHeight: 300,
                  maxHeight: 600,
                  transition: "border-color 0.2s",
                  flex: 1,
                }}
              />

              {jsonError && (
                <div style={{ color: C.error, fontSize: 12 }}>⚠ {jsonError}</div>
              )}

              {/* Options */}
              <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
                <label style={{
                  display: "flex", alignItems: "center", gap: 7,
                  fontSize: 12, color: C.dim, cursor: "pointer",
                }}>
                  <input
                    type="checkbox"
                    checked={includeAudit}
                    onChange={e => setIncludeAudit(e.target.checked)}
                    style={{ accentColor: C.accent }}
                  />
                  Include audit report
                </label>
              </div>

              <button onClick={run} disabled={loading || !!jsonError} style={{
                background: loading ? C.muted : `linear-gradient(135deg, ${C.accent}, #6B9EF8)`,
                color: "#fff", border: "none", borderRadius: 10,
                padding: "12px 20px", fontSize: 14, fontWeight: 600,
                cursor: loading ? "wait" : "pointer",
                fontFamily: "inherit", transition: "all 0.2s",
                display: "flex", alignItems: "center",
                justifyContent: "center", gap: 8,
                width: "100%",
              }}>
                {loading ? (
                  <>
                    <div style={{
                      width: 14, height: 14,
                      border: "2px solid rgba(255,255,255,0.3)",
                      borderTopColor: "#fff",
                      borderRadius: "50%",
                      animation: "spin 0.7s linear infinite",
                    }} />
                    De-identifying...
                  </>
                ) : (
                  <>🛡️ De-identify {isBundle ? "Bundle" : "Resource"}</>
                )}
              </button>

              {error && (
                <div style={{
                  background: C.error + "15",
                  border: `1px solid ${C.error}40`,
                  borderRadius: 8, padding: 12,
                  color: C.error, fontSize: 13,
                }}>{error}</div>
              )}
            </div>

            {/* Right — Output */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%" }}>
              <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                De-identified Output
              </div>

              {deidentifiedData ? (
                <>
                  {/* Status bar */}
                  <div style={{
                    display: "flex", alignItems: "center", gap: 8,
                    background: C.teal + "0F",
                    border: `1px solid ${C.teal}30`,
                    borderRadius: 8, padding: "8px 14px",
                  }}>
                    <div style={{
                      width: 7, height: 7, borderRadius: "50%",
                      background: C.teal,
                    }} />
                    <span style={{ fontSize: 13, color: C.teal, fontWeight: 500 }}>
                      De-identification complete · Mode: {mode} · HIPAA Safe Harbor
                    </span>
                  </div>

                  <div style={{ flex: 1, minHeight: 300, display: "flex", flexDirection: "column" }}>
                    <JsonBlock data={deidentifiedData} maxHeight={600} />
                  </div>

                  {/* Audit report */}
                  {includeAudit && auditReport && (
                    <AuditPanel report={auditReport} />
                  )}
                </>
              ) : (
                <div style={{
                  background: C.surface,
                  border: `1px solid ${C.border}`,
                  borderRadius: 10,
                  minHeight: 300,
                  height: "100%",
                  display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center",
                  gap: 12, color: C.muted,
                  padding: 20,
                  flex: 1,
                }}>
                  <span style={{ fontSize: 40 }}>🛡️</span>
                  <div style={{ fontSize: 14 }}>
                    De-identified resource will appear here
                  </div>
                  <div style={{ fontSize: 12, color: C.border }}>
                    Select a mode and click De-identify
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── PHI categories info ── */}
        <div style={{
          marginTop: 24,
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 14, padding: "16px 20px",
        }}>
          <div style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: 700, fontSize: 13, marginBottom: 14,
            display: "flex", alignItems: "center", gap: 8,
          }}>
            <span>📋</span>
            HIPAA Safe Harbor — 18 Identifier Categories Covered
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {[
              "Names", "Geographic data", "Dates (year kept)",
              "Phone numbers", "Fax numbers", "Email addresses",
              "SSN / National IDs", "Medical record numbers",
              "Health plan numbers", "Account numbers",
              "Certificate numbers", "Vehicle identifiers",
              "Device identifiers", "Web URLs", "IP addresses",
              "Biometric identifiers", "Photos (removed)", "Unique identifiers",
            ].map(item => (
              <Tag key={item} color={C.teal}>{item}</Tag>
            ))}
          </div>
          <div style={{ marginTop: 14, fontSize: 11, color: C.muted, lineHeight: 1.5 }}>
            Standard: <span style={{ color: C.dim }}>HIPAA Safe Harbor (45 CFR §164.514(b))</span>
            &nbsp;·&nbsp;
            Pseudonymize mode is deterministic — same input always produces the same fake output, ensuring consistency across a bundle.
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        * { box-sizing: border-box; }
        textarea { tab-size: 2; }
        
        @media (min-width: 768px) {
          .desktop-grid {
            grid-template-columns: 1fr 1fr !important;
            align-items: stretch !important;
          }
          .desktop-text-grid {
            grid-template-columns: 1fr 1fr !important;
          }
        }
        
        @media (max-width: 767px) {
          .mobile-text-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}