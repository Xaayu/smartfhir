import { useState, useEffect, createContext, useContext, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";

// Theme Context
const ThemeContext = createContext();

const THEMES = {
  dark: {
    bg: "#0F1117",
    surface: "#1A1D27",
    border: "#2A2D3E",
    accent: "#4F8EF7",
    accentDim: "#1E3A6E",
    success: "#34D399",
    warning: "#FBBF24",
    error: "#F87171",
    muted: "#6B7280",
    text: "#E2E8F0",
    textDim: "#94A3B8",
    shadow: "rgba(0, 0, 0, 0.3)",
    shadowLight: "rgba(79, 142, 247, 0.1)",
  },
  light: {
    bg: "#F8FAFC",
    surface: "#FFFFFF",
    border: "#E2E8F0",
    accent: "#3B82F6",
    accentDim: "#DBEAFE",
    success: "#10B981",
    warning: "#F59E0B",
    error: "#EF4444",
    muted: "#64748B",
    text: "#1E293B",
    textDim: "#64748B",
    shadow: "rgba(0, 0, 0, 0.1)",
    shadowLight: "rgba(59, 130, 246, 0.1)",
  },
};

function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("smartfhirTheme");
    return saved || "dark";
  });

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("smartfhirTheme", newTheme);
  };

  const colors = THEMES[theme];

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, colors }}>
      {children}
    </ThemeContext.Provider>
  );
}

const GRADE_COLORS = {
  "A+": "#10B981", A: "#10B981", B: "#3B82F6",
  C: "#F59E0B", D: "#EF4444",
};

const SAMPLE_DATA = {
  Patient: {
    PtID: "P101", first_name: "John", last_name: "Doe",
    Sex: "M", DOB: "15/04/1990", marital: "married",
    language: "English", phone: "555-1234", email: "john@example.com",
  },
  Observation: {
    TestName: "Blood Pressure", Value: "120", Unit: "mmHg",
    PatientID: "P101", Date: "15/01/2024",
    Status: "final", Interpretation: "N",
  },
  Condition: {
    PatientID: "P101", Diagnosis: "Diabetes Type 2",
    Status: "ongoing", Severity: "serious",
    VerificationStatus: "yes", OnsetDate: "15/06/2023",
    RecordedDate: "20/06/2023", Note: "Patient on insulin therapy",
  },
  Encounter: {
    subject: "P101",
    status: "finished",
    class: "ambulatory",
    "period.start": "2024-01-01",
    "period.end": "2024-01-02",
    reasonCode: "Routine check",
  },
  MedicationRequest: {
    medication: "metformin",
    subject: "P101",
    status: "active",
    intent: "order",
    "dosageInstruction.dose": 500,
    "dosageInstruction.unit": "mg",
    "dispenseRequest.quantity": 30,
  },
};

const ENDPOINTS = {
  Patient: "/map-and-validate",
  Observation: "/observation/map-validate",
  Condition: "/condition/map-validate",
  Encounter: "/encounter/map-validate",
  MedicationRequest: "/medication/map-validate",
};

const WORKFLOW_STEPS = [
  { title: "Refine map fields", subtitle: "Align source data to clean FHIR attributes" },
  { title: "Lookup codes", subtitle: "Resolve LOINC, SNOMED, RxNorm values" },
  { title: "Validate", subtitle: "Check required fields and FHIR rules" },
  { title: "Auto-fix", subtitle: "Apply safe repairs and normalization" },
  { title: "Score", subtitle: "Review quality and readiness" },
];

function getApiHeaders() {
  const apiKey = localStorage.getItem("smartfhirApiKey");
  return {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  };
}

function extractPositionFromError(msg) {
  // try to extract 'position N' or 'at line X column Y'
  const posMatch = msg.match(/position\s*(\d+)/i);
  if (posMatch) return parseInt(posMatch[1], 10);
  const lcMatch = msg.match(/line\s*(\d+)\s*column\s*(\d+)/i);
  if (lcMatch) return { line: parseInt(lcMatch[1], 10), column: parseInt(lcMatch[2], 10) };
  return null;
}

function tryParseJSON(str) {
  try {
    return { ok: true, value: JSON.parse(str) };
  } catch (e) {
    return { ok: false, message: e.message || String(e), pos: extractPositionFromError(e.message || '') };
  }
}

function autoFixJSON(str) {
  // common heuristics: replace single quotes with double quotes, remove trailing commas
  let s = str;
  // replace smart quotes
  s = s.replace(/[“”]/g, '"').replace(/[‘’]/g, "'");
  // replace single quotes with double quotes (risky but helpful for common mistakes)
  s = s.replace(/'(.*?)'(?=\s*:)/g, '"$1"'); // keys
  s = s.replace(/:\s*'(.*?)'/g, ':"$1"'); // values
  // remove trailing commas before } or ]
  s = s.replace(/,\s*(}[\]])/g, '$1');
  s = s.replace(/,\s*([}\]])/g, '$1');
  // attempt parse
  const parsed = tryParseJSON(s);
  if (parsed.ok) return s;
  return null;
}

function Badge({ children, color, colors }) {
  return (
    <span style={{
      background: color + "22", color, border: `1px solid ${color}44`,
      borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600,
      letterSpacing: "0.05em", textTransform: "uppercase",
      transition: "all 0.2s ease",
    }}>{children}</span>
  );
}



function GradeRing({ grade, colors }) {
  const color = GRADE_COLORS[grade] || colors.muted;
  return (
    <div style={{
      width: 64, height: 64, borderRadius: "50%",
      border: `3px solid ${color}`,
      display: "flex", alignItems: "center", justifyContent: "center",
      color, fontSize: 22, fontWeight: 700,
      boxShadow: `0 0 16px ${color}44`,
      transition: "all 0.3s ease",
    }}>{grade}</div>
  );
}

function Pill({ label, value, color, colors }) {
  return (
    <div style={{
      background: colors.surface, border: `1px solid ${colors.border}`,
      borderRadius: 8, padding: "10px 16px", flex: 1, minWidth: 100,
      boxShadow: `0 2px 8px ${colors.shadow}`,
      transition: "all 0.3s ease",
    }}>
      <div style={{ color: colors.textDim, fontSize: 11, marginBottom: 4, fontWeight: 600 }}>{label}</div>
      <div style={{ color: color || colors.text, fontSize: 20, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function ResultsBlankState({ colors }) {
  const skeletonRows = [
    { width: "72%", color: colors.error },
    { width: "54%", color: colors.warning },
    { width: "64%", color: colors.success },
  ];

  return (
    <div style={{
      flex: 1,
      minHeight: 320,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: colors.muted,
      padding: 24,
    }}>
      <div style={{
        width: "min(100%, 420px)",
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
        background: colors.surface,
        padding: 24,
        boxShadow: `0 16px 40px ${colors.shadow}`,
        transition: "all 0.3s ease",
      }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 18 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: colors.accent + "18",
            border: `1px solid ${colors.accent}33`,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: colors.accent, fontWeight: 800, fontSize: 16,
          }}>V</div>
          <div style={{ flex: 1 }}>
            <div style={{ color: colors.text, fontSize: 15, fontWeight: 700 }}>
              Ready for validation
            </div>
            <div style={{ color: colors.textDim, fontSize: 12, marginTop: 3 }}>
              Results, mapping notes, and FHIR output will appear here.
            </div>
          </div>
        </div>

        <div aria-hidden="true" style={{
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          padding: 14,
          display: "flex",
          flexDirection: "column",
          gap: 12,
          opacity: 0.82,
        }}>
          <div style={{ display: "flex", gap: 8 }}>
            {[colors.error, colors.warning, colors.success].map(color => (
              <div key={color} style={{
                height: 32,
                flex: 1,
                borderRadius: 6,
                background: color + "10",
                border: `1px solid ${color}22`,
              }} />
            ))}
          </div>
          {skeletonRows.map(row => (
            <div key={row.width} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: row.color + "88",
              }} />
              <div style={{
                height: 9,
                width: row.width,
                borderRadius: 999,
                background: `linear-gradient(90deg, ${colors.border}, ${row.color}33)`,
              }} />
            </div>
          ))}
        </div>

        <div style={{
          marginTop: 14,
          borderTop: `1px solid ${colors.border}`,
          paddingTop: 12,
          color: colors.textDim,
          fontSize: 12,
          lineHeight: 1.5,
        }}>
          Run validation to see mapping notes, quality checks, and the generated FHIR resource.
        </div>
      </div>
    </div>
  );
}

function renderValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch (e) {
    return String(value);
  }
}

function ErrorCard({ err, colors }) {
  const isFixed = !!err.fix;
  return (
    <div style={{
      background: colors.bg, border: `1px solid ${isFixed ? colors.accentDim : colors.error + "44"}`,
      borderRadius: 8, padding: 14, marginBottom: 8,
      boxShadow: `0 2px 8px ${colors.shadow}`,
      transition: "all 0.3s ease",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ color: colors.accent, fontFamily: "monospace", fontSize: 13 }}>
          {renderValue(err.field)}
        </span>
        <Badge color={isFixed ? colors.success : colors.error} colors={colors}>
          {isFixed ? "auto-fixed" : "needs review"}
        </Badge>
      </div>
      <div style={{ color: colors.textDim, fontSize: 13, marginBottom: 6 }}>{renderValue(err.explanation || err.message)}</div>
      {isFixed && (
        <div style={{
          display: "flex", gap: 8, alignItems: "center",
          fontFamily: "monospace", fontSize: 12,
        }}>
          <span style={{
            background: colors.error + "22", color: colors.error,
            padding: "2px 8px", borderRadius: 4,
          }}>{renderValue(err.received)}</span>
          <span style={{ color: colors.muted }}>→</span>
          <span style={{
            background: colors.success + "22", color: colors.success,
            padding: "2px 8px", borderRadius: 4,
          }}>{renderValue(err.fix)}</span>
        </div>
      )}
      {err.suggested_fix && !isFixed && (
        <div style={{ color: colors.warning, fontSize: 12, marginTop: 4 }}>
          💡 {renderValue(err.suggested_fix)}
        </div>
      )}
    </div>
  );
}

function WarningCard({ w, colors }) {
  return (
    <div style={{
      background: colors.bg, border: `1px solid ${colors.warning}44`,
      borderRadius: 8, padding: 14, marginBottom: 8,
      boxShadow: `0 2px 8px ${colors.shadow}`,
      transition: "all 0.3s ease",
    }}>
      <div style={{ color: colors.warning, fontFamily: "monospace", fontSize: 13, marginBottom: 4 }}>
        {renderValue(w.field)}
      </div>
      <div style={{ color: colors.textDim, fontSize: 13 }}>{renderValue(w.message)}</div>
      {w.suggestion && (
        <div style={{ color: colors.accent, fontSize: 12, marginTop: 4 }}>→ {renderValue(w.suggestion)}</div>
      )}
    </div>
  );
}

function JsonBlock({ data, resourceType, colors }) {
  const [copied, setCopied] = useState(false);
  const jsonText = JSON.stringify(data, null, 2);

  async function copyJson() {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(jsonText);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = jsonText;
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "0";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch (e) {
      console.error("Could not copy FHIR output", e);
    }
  }

  function downloadJson() {
    const blob = new Blob([jsonText], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${resourceType || "fhir"}-resource.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  return (
    <div style={{
      background: colors.bg,
      border: `1px solid ${colors.border}`,
      borderRadius: 8,
      overflow: "hidden",
      boxShadow: `0 2px 8px ${colors.shadow}`,
      transition: "all 0.3s ease",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        padding: "10px 12px",
        borderBottom: `1px solid ${colors.border}`,
        background: colors.surface,
      }}>
        <div>
          <div style={{ color: colors.textDim, fontSize: 12, letterSpacing: "0.08em" }}>
            FHIR JSON {resourceType ? `• ${resourceType}` : ""}
          </div>
          <div style={{ color: colors.text, fontSize: 13, fontWeight: 700 }}>
            {Object.keys(data || {}).length} fields
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={downloadJson} style={{
            background: colors.surface,
            color: colors.text,
            border: `1px solid ${colors.border}`,
            borderRadius: 6,
            padding: "6px 10px",
            fontSize: 12,
            fontWeight: 700,
            cursor: "pointer",
            transition: "all 0.2s ease",
            boxShadow: "0 1px 4px rgba(0, 0, 0, 0.1)",
          }}>
            Download
          </button>
          <button onClick={copyJson} style={{
            background: copied ? colors.success : colors.bg,
            color: copied ? "#000" : colors.text,
            border: `1px solid ${copied ? colors.success : colors.border}`,
            borderRadius: 6,
            padding: "6px 10px",
            fontSize: 12,
            fontWeight: 700,
            cursor: "pointer",
            minWidth: 76,
            transition: "all 0.2s ease",
            boxShadow: "0 1px 4px rgba(0, 0, 0, 0.1)",
          }}>
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>
      <pre style={{
        padding: 16, fontSize: 12,
        color: colors.textDim, overflowX: "auto",
        fontFamily: "monospace", lineHeight: 1.6, margin: 0,
      }}>{jsonText}</pre>
    </div>
  );
}

function getResourceIcon(resourceType) {
  switch (resourceType) {
    case "Patient": return "👤";
    case "Observation": return "🧪";
    case "Condition": return "❤️";
    case "Encounter": return "🏥";
    case "MedicationRequest": return "💊";
    case "Practitioner": return "👨‍⚕️";
    case "Medication": return "💊";
    default: return "📄";
  }
}

function getResourceSummary(resource) {
  if (!resource || typeof resource !== "object") return [];
  const type = resource.resourceType;
  const children = [];

  const safe = (path) => {
    return path.split(".").reduce((acc, key) => acc && acc[key], resource);
  };

  const nameValue = () => {
    if (Array.isArray(resource.name) && resource.name[0]) {
      const first = resource.name[0];
      const family = first.family || "";
      const given = Array.isArray(first.given) ? first.given.join(" ") : "";
      return `${given}${family ? ` ${family}` : ""}`.trim();
    }
    if (resource.name && typeof resource.name === "string") return resource.name;
    return null;
  };

  const codableDisplay = (cc) => {
    if (!cc) return null;
    if (typeof cc === "string") return cc;
    if (Array.isArray(cc?.coding) && cc.coding[0]?.display) return cc.coding[0].display;
    if (cc.text) return cc.text;
    return null;
  };

  switch (type) {
    case "Patient":
      children.push(["Name", nameValue() || safe("name.0.text") || safe("name.0.family") || safe("name.0.given")]);
      children.push(["Gender", resource.gender]);
      children.push(["BirthDate", resource.birthDate]);
      if (Array.isArray(resource.identifier) && resource.identifier.length) {
        children.push(["Identifier", resource.identifier[0].value || resource.identifier[0].system]);
      }
      break;
    case "Observation":
      children.push(["Code", codableDisplay(resource.code) || resource.code?.text]);
      children.push(["Value", safe("valueQuantity.value") || safe("valueString") || safe("valueCodeableConcept.text")]);
      children.push(["Unit", safe("valueQuantity.unit")]);
      children.push(["Subject", safe("subject.reference") || safe("subject.display")]);
      break;
    case "Condition":
      children.push(["Code", codableDisplay(resource.code) || resource.code?.text]);
      children.push(["Clinical status", safe("clinicalStatus.coding.0.display") || safe("clinicalStatus.text")]);
      children.push(["Severity", safe("severity.coding.0.display") || safe("severity.text")]);
      break;
    case "Encounter":
      children.push(["Class", safe("class.coding.0.display") || safe("class.code")]);
      children.push(["Period", `${safe("period.start") || "?"} → ${safe("period.end") || "?"}`]);
      children.push(["Subject", safe("subject.reference")]);
      break;
    case "MedicationRequest":
      children.push(["Drug", codableDisplay(resource.medicationCodeableConcept) || safe("medicationReference.display")]);
      children.push(["Dosage", safe("dosageInstruction.0.text") || `${safe("dosageInstruction.0.doseAndRate.0.doseQuantity.value") || safe("dosageInstruction.0.doseAndRate.0.doseQuantity.value")} ${safe("dosageInstruction.0.doseAndRate.0.doseQuantity.unit") || ""}`.trim()]);
      children.push(["Status", resource.status]);
      break;
    case "Medication":
      children.push(["Name", resource.code?.text || resource.code?.coding?.[0]?.display || resource.name]);
      break;
    default:
      if (resource.code || resource.text) {
        children.push(["Text", resource.text || codableDisplay(resource.code)]);
      }
      break;
  }

  return children.filter(([key, value]) => value !== undefined && value !== null && value !== "");
}

function getBundleEntries(bundle) {
  if (!bundle || bundle.resourceType !== "Bundle" || !Array.isArray(bundle.entry)) return [];
  return bundle.entry.map((entry, idx) => {
    const resource = entry?.resource || {};
    const title = resource.resourceType || `Entry ${idx + 1}`;
    const summary = getResourceSummary(resource);
    return {
      key: entry.fullUrl || `${title}-${idx}`,
      title,
      subtitle: resource.id || entry.fullUrl || "",
      icon: getResourceIcon(resource.resourceType),
      summary,
      resource,
    };
  });
}

function TreeRow({ label, value, colors }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginTop: 4 }}>
      <span style={{ color: colors.textDim, fontSize: 12 }}>{label}</span>
      <span style={{ color: colors.text, fontSize: 12, fontWeight: 600, textAlign: "right", maxWidth: "65%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{value}</span>
    </div>
  );
}

function BundleExplorer({ data, colors }) {
  if (!data || data.resourceType !== "Bundle") {
    return (
      <div style={{ padding: 24, color: colors.textDim, fontSize: 13 }}>
        Bundle Explorer requires a FHIR Bundle resource.
      </div>
    );
  }

  const entries = getBundleEntries(data);

  return (
    <div style={{
      background: colors.bg,
      border: `1px solid ${colors.border}`,
      borderRadius: 12,
      padding: 20,
      boxShadow: `0 2px 18px ${colors.shadow}`,
      overflow: "auto",
      maxHeight: 760,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
        <div style={{ width: 38, height: 38, borderRadius: 10, background: colors.accent, display: "grid", placeItems: "center", color: "#fff", fontSize: 18 }}>📦</div>
        <div>
          <div style={{ color: colors.text, fontSize: 16, fontWeight: 700 }}>Bundle Explorer</div>
          <div style={{ color: colors.textDim, fontSize: 12 }}>Visualize resources and key fields without reading raw JSON.</div>
        </div>
      </div>
      {entries.length === 0 ? (
        <div style={{ color: colors.textDim }}>No bundle entries found.</div>
      ) : (
        <div style={{ display: "grid", gap: 14 }}>
          {entries.map(entry => (
            <div key={entry.key} style={{
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              padding: 16,
              background: colors.surface,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <span style={{ fontSize: 18 }}>{entry.icon}</span>
                <div style={{ display: "grid", gap: 2 }}>
                  <div style={{ color: colors.text, fontSize: 14, fontWeight: 700 }}>{entry.title}</div>
                  {entry.subtitle ? <div style={{ color: colors.textDim, fontSize: 12 }}>{entry.subtitle}</div> : null}
                </div>
              </div>
              <div style={{ display: "grid", gap: 4 }}>
                {entry.summary.map(([name, value]) => (
                  <TreeRow key={name} label={name} value={String(value)} colors={colors} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Notifications({ items, remove }) {
  return (
    <div style={{ position: 'fixed', right: 20, top: 80, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map(it => (
        <div key={it.id} style={{
          background: it.type === 'error' ? '#2b0b0b' : it.type === 'success' ? '#0b2b12' : '#0b2540',
          color: '#fff', borderRadius: 8, padding: '8px 12px', minWidth: 200,
          boxShadow: '0 6px 18px rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'space-between', gap: 8,
        }}>
          <div style={{ fontSize: 13 }}>{renderValue(it.message)}</div>
          <button onClick={() => remove(it.id)} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer' }}>✕</button>
        </div>
      ))}
    </div>
  );
}

function MappingRow({ rule, colors }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "6px 0", borderBottom: `1px solid ${colors.border}`,
      fontFamily: "monospace", fontSize: 12,
      transition: "all 0.2s ease",
    }}>
      <span style={{ color: colors.warning, minWidth: 120 }}>{renderValue(rule.original_field)}</span>
      <span style={{ color: colors.muted }}>→</span>
      <span style={{ color: colors.success, flex: 1 }}>{renderValue(rule.mapped_to)}</span>
      <Badge color={rule.rule_type === "built_in" ? colors.accent : colors.success} colors={colors}>
        {renderValue(rule.rule_type)}
      </Badge>
    </div>
  );
}

const TEXTAREA_STYLE = {
  flex: 1,
  borderRadius: 8,
  padding: 12,
  fontFamily: "monospace",
  fontSize: 12,
  lineHeight: 1.6,
  resize: "vertical",
  outline: "none",
};

function BundlePanel({ onNotify, isMobile }) {
  const { colors } = useTheme();
  const [inputMode, setInputMode] = useState("unified"); // "unified" or "separate"
  const [unifiedInput, setUnifiedInput] = useState(JSON.stringify({
    Patient: SAMPLE_DATA.Patient,
    Observation: [SAMPLE_DATA.Observation],
    Condition: [SAMPLE_DATA.Condition],
    Encounter: SAMPLE_DATA.Encounter,
    MedicationRequest: [SAMPLE_DATA.MedicationRequest],
    bundle_type: "collection"
  }, null, 2));
  const [patientInput, setPatientInput] = useState(JSON.stringify(SAMPLE_DATA.Patient, null, 2));
  const [observationsInput, setObservationsInput] = useState(JSON.stringify([SAMPLE_DATA.Observation], null, 2));
  const [conditionsInput, setConditionsInput] = useState(JSON.stringify([SAMPLE_DATA.Condition], null, 2));
  const [encountersInput, setEncountersInput] = useState(JSON.stringify([SAMPLE_DATA.Encounter], null, 2));
  const [medicationsInput, setMedicationsInput] = useState(JSON.stringify([SAMPLE_DATA.MedicationRequest], null, 2));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("resource");

  function parseJsonArray(value, label) {
    const parsed = tryParseJSON(value);
    if (!parsed.ok) {
      throw new Error(`Invalid ${label} JSON: ${parsed.message}`);
    }
    if (Array.isArray(parsed.value)) {
      return parsed.value;
    }
    if (parsed.value && typeof parsed.value === "object") {
      return [parsed.value];
    }
    return [];
  }

  function prettyFormatInput(value, setter, label) {
    const parsed = tryParseJSON(value);
    if (!parsed.ok) {
      onNotify && onNotify(`Cannot pretty-format ${label}: ${parsed.message}`, "error");
      return;
    }
    setter(JSON.stringify(parsed.value, null, 2));
    onNotify && onNotify(`Formatted ${label} JSON`, "success");
  }

  async function generateBundle() {
    setLoading(true);
    setError(null);
    setResult(null);
    onNotify && onNotify("Generating bundle...", "info");

    try {
      let payload;
      let endpoint;

      if (inputMode === "unified") {
        const unifiedParse = tryParseJSON(unifiedInput);
        if (!unifiedParse.ok) {
          throw new Error(`Invalid unified JSON: ${unifiedParse.message}`);
        }
        payload = unifiedParse.value;
        endpoint = "/unified-bundle";
      } else {
        const patientParse = tryParseJSON(patientInput);
        if (!patientParse.ok) {
          throw new Error(`Invalid patient JSON: ${patientParse.message}`);
        }
        if (!patientParse.value || typeof patientParse.value !== "object" || Array.isArray(patientParse.value)) {
          throw new Error("Patient input must be a JSON object.");
        }

        payload = {
          patient: patientParse.value,
          observations: parseJsonArray(observationsInput, "observations"),
          conditions: parseJsonArray(conditionsInput, "conditions"),
          encounters: parseJsonArray(encountersInput, "encounters"),
          medications: parseJsonArray(medicationsInput, "medications"),
        };
        endpoint = "/bundle";
      }

      const res = await fetch(API_BASE + endpoint, {
        method: "POST",
        headers: getApiHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.error || data.message || "Bundle generation failed.");
      }

      setResult(data);
      onNotify && onNotify("Bundle generated successfully", "success");
    } catch (e) {
      setError(e.message || "Could not generate bundle");
      onNotify && onNotify(e.message || "Could not generate bundle", "error");
    } finally {
      setLoading(false);
    }
  }

  const quality = result?.quality;
  const errors = result?.validation?.errors || result?.errors || [];
  const warnings = result?.validation?.warnings || result?.warnings || [];
  const mappingRules = result?.mapping?.applied_rules || result?.applied_rules || [];
  const unmapped = result?.mapping?.unmapped_fields || result?.unmapped_fields || [];
  const fhirResource = result?.fixed_resource || result?.fhir_resource || result?.mapped_resource || result;

  const TABS = [
    { id: "errors", label: `Errors (${errors.length})` },
    { id: "warnings", label: `Warnings (${warnings.length})` },
    { id: "mapping", label: `Mapping (${mappingRules.length})` },
    { id: "resource", label: "FHIR Output" },
    { id: "explorer", label: "Bundle Explorer" },
  ];

  return (
    <div style={{ display: isMobile ? "block" : "flex", gap: isMobile ? 16 : 20, height: "100%" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ color: colors.textDim, fontSize: 12, letterSpacing: "0.08em", fontWeight: 600 }}>
            BUNDLE INPUTS
          </div>
          <div style={{ display: "flex", gap: 4 }}>
            <button 
              onClick={() => setInputMode("unified")}
              style={{
                background: inputMode === "unified" ? colors.accent : colors.surface,
                color: inputMode === "unified" ? "#fff" : colors.text,
                border: `1px solid ${colors.border}`,
                borderRadius: 6,
                padding: "4px 12px",
                fontSize: 11,
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              Unified
            </button>
            <button 
              onClick={() => setInputMode("separate")}
              style={{
                background: inputMode === "separate" ? colors.accent : colors.surface,
                color: inputMode === "separate" ? "#fff" : colors.text,
                border: `1px solid ${colors.border}`,
                borderRadius: 6,
                padding: "4px 12px",
                fontSize: 11,
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              Separate
            </button>
          </div>
        </div>
        {inputMode === "unified" ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <label style={{ color: colors.textDim, fontSize: 12, fontWeight: 600 }}>Unified Bundle JSON</label>
              <button onClick={() => prettyFormatInput(unifiedInput, setUnifiedInput, "Unified")} style={{
                background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                borderRadius: 4, padding: "4px 8px", fontSize: 11, fontWeight: 600, cursor: 'pointer',
                transition: "all 0.2s ease",
              }}>Pretty format</button>
            </div>
            <textarea value={unifiedInput} onChange={e => setUnifiedInput(e.target.value)} style={{ minHeight: isMobile ? 300 : 400, ...TEXTAREA_STYLE, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
          </div>
        ) : (
          <div style={{ display: "grid", gap: 12, gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ color: colors.textDim, fontSize: 12, fontWeight: 600 }}>Patient</label>
                <button onClick={() => prettyFormatInput(patientInput, setPatientInput, "Patient")} style={{
                  background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                  borderRadius: 4, padding: "4px 8px", fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  transition: "all 0.2s ease",
                }}>Pretty format</button>
              </div>
              <textarea value={patientInput} onChange={e => setPatientInput(e.target.value)} style={{ minHeight: isMobile ? 150 : 180, ...TEXTAREA_STYLE, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ color: colors.textDim, fontSize: 12, fontWeight: 600 }}>Observations</label>
                <button onClick={() => prettyFormatInput(observationsInput, setObservationsInput, "Observations")} style={{
                  background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                  borderRadius: 4, padding: "4px 8px", fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  transition: "all 0.2s ease",
                }}>Pretty format</button>
              </div>
              <textarea value={observationsInput} onChange={e => setObservationsInput(e.target.value)} style={{ minHeight: isMobile ? 150 : 180, ...TEXTAREA_STYLE, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ color: colors.textDim, fontSize: 12, fontWeight: 600 }}>Conditions</label>
                <button onClick={() => prettyFormatInput(conditionsInput, setConditionsInput, "Conditions")} style={{
                  background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                  borderRadius: 4, padding: "4px 8px", fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  transition: "all 0.2s ease",
                }}>Pretty format</button>
              </div>
              <textarea value={conditionsInput} onChange={e => setConditionsInput(e.target.value)} style={{ minHeight: isMobile ? 150 : 180, ...TEXTAREA_STYLE, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ color: colors.textDim, fontSize: 12, fontWeight: 600 }}>Encounters</label>
                <button onClick={() => prettyFormatInput(encountersInput, setEncountersInput, "Encounters")} style={{
                  background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                  borderRadius: 4, padding: "4px 8px", fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  transition: "all 0.2s ease",
                }}>Pretty format</button>
              </div>
              <textarea value={encountersInput} onChange={e => setEncountersInput(e.target.value)} style={{ minHeight: isMobile ? 150 : 180, ...TEXTAREA_STYLE, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ color: colors.textDim, fontSize: 12, fontWeight: 600 }}>Medications</label>
                <button onClick={() => prettyFormatInput(medicationsInput, setMedicationsInput, "Medications")} style={{
                  background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                  borderRadius: 4, padding: "4px 8px", fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  transition: "all 0.2s ease",
                }}>Pretty format</button>
              </div>
              <textarea value={medicationsInput} onChange={e => setMedicationsInput(e.target.value)} style={{ minHeight: isMobile ? 150 : 180, ...TEXTAREA_STYLE, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
            </div>
          </div>
        )}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {result ? (
            <>
              <button onClick={generateBundle} disabled={loading} style={{
                flex: isMobile ? "1 1 100%" : 1, background: loading ? colors.accentDim : colors.accent,
                color: "#fff", border: "none", borderRadius: 8,
                padding: "10px 0", fontWeight: 600, cursor: loading ? "wait" : "pointer",
                fontSize: 14, transition: "all 0.3s ease",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              }}>
                {loading ? "Processing..." : "Re-run"}
              </button>
              <button style={{
                flex: isMobile ? "1 1 100%" : 1, background: colors.success, color: "#000", border: "none",
                borderRadius: 8, padding: "10px 0", fontWeight: 700, fontSize: 14,
                transition: "all 0.3s ease",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              }}>✓ Done</button>
            </>
          ) : (
            <button onClick={generateBundle} disabled={loading} style={{
              flex: 1, background: loading ? colors.accentDim : colors.accent,
              color: "#fff", border: "none", borderRadius: 8,
              padding: "10px 0", fontWeight: 600, cursor: loading ? "wait" : "pointer",
              fontSize: 14, transition: "all 0.3s ease",
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
            }}>
              {loading ? "Generating..." : "Generate Bundle"}
            </button>
          )}
        </div>
        {error && (
          <div style={{ background: colors.error + "22", border: `1px solid ${colors.error}44`, borderRadius: 8, padding: 12, color: colors.error, fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>
      <div style={{ flex: 1.2, display: "flex", flexDirection: "column", gap: 12 }}>
        {result ? (
          <>
            {/* Quality + Stats */}
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <GradeRing grade={quality?.grade || "—"} colors={colors} />
              <div style={{ display: "flex", gap: 8, flex: 1, flexWrap: "wrap" }}>
                <Pill label="Errors Found" value={quality?.total_errors_found ?? errors.length} color={colors.error} colors={colors} />
                <Pill label="Auto-Fixed" value={quality?.errors_auto_fixed ?? 0} color={colors.success} colors={colors} />
                <Pill label="Remaining" value={quality?.remaining_errors ?? 0} color={quality?.remaining_errors > 0 ? colors.warning : colors.success} colors={colors} />
                <Pill label="Score" value={`${quality?.score ?? 0}%`} color={colors.accent} colors={colors} />
              </div>
            </div>

            {/* Status bar */}
            <div style={{
              display: "flex", gap: 8, alignItems: "center",
              background: colors.bg, border: `1px solid ${colors.border}`,
              borderRadius: 8, padding: "8px 14px",
              boxShadow: `0 2px 8px ${colors.shadow}`,
              transition: "all 0.3s ease",
            }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: (result?.validation?.final_valid || result?.valid)
                  ? colors.success : colors.error,
              }} />
              <span style={{ color: colors.textDim, fontSize: 13 }}>
                {(result?.validation?.final_valid || result?.valid)
                  ? "Bundle is valid after fixes"
                  : `${errors.filter(e => !e.fix).length} error(s) require manual review`}
              </span>
              {unmapped.length > 0 && (
                <Badge color={colors.warning} colors={colors}>{unmapped.length} unmapped</Badge>
              )}
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: 4, borderBottom: `1px solid ${colors.border}` }}>
              {TABS.map(t => (
                <button key={t.id} onClick={() => setTab(t.id)} style={{
                  background: "none", border: "none",
                  borderBottom: tab === t.id ? `2px solid ${colors.accent}` : "2px solid transparent",
                  color: tab === t.id ? colors.accent : colors.muted,
                  padding: "8px 14px", cursor: "pointer", fontSize: 13,
                  fontWeight: tab === t.id ? 600 : 400, marginBottom: -1,
                  transition: "all 0.2s ease",
                }}>{t.label}</button>
              ))}
            </div>

            {/* Tab content */}
            <div style={{ flex: 1, overflowY: "auto" }}>
              {tab === "errors" && (
                errors.length === 0
                  ? <div style={{ color: colors.success, padding: 20, textAlign: "center" }}>✓ No errors found</div>
                  : errors.map((e, i) => <ErrorCard key={i} err={e} colors={colors} />)
              )}
              {tab === "warnings" && (
                warnings.length === 0
                  ? <div style={{ color: colors.muted, padding: 20, textAlign: "center" }}>No warnings</div>
                  : warnings.map((w, i) => <WarningCard key={i} w={w} colors={colors} />)
              )}
              {tab === "mapping" && (
                <div>
                  {mappingRules.map((r, i) => <MappingRow key={i} rule={r} colors={colors} />)}
                  {unmapped.length > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <div style={{ color: colors.warning, fontSize: 12, marginBottom: 8, fontWeight: 600 }}>
                        UNMAPPED FIELDS
                      </div>
                      {unmapped.map((u, i) => (
                        <div key={i} style={{
                          display: "flex", justifyContent: "space-between",
                          padding: "6px 0", borderBottom: `1px solid ${colors.border}`,
                          fontFamily: "monospace", fontSize: 12,
                          transition: "all 0.2s ease",
                        }}>
                          <span style={{ color: colors.warning }}>{renderValue(u.field)}</span>
                          <span style={{ color: colors.muted, whiteSpace: "pre-wrap", textAlign: "right" }}>{renderValue(u.value)}</span>
                          <Badge color={colors.warning} colors={colors}>unmapped</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {tab === "resource" && fhirResource && <JsonBlock data={fhirResource} resourceType="Bundle" colors={colors} />}
              {tab === "explorer" && fhirResource && <BundleExplorer data={fhirResource} colors={colors} />}
            </div>
          </>
        ) : (
          <ResultsBlankState colors={colors} />
        )}
      </div>
    </div>
  );
}

function ResourcePanel({ type, onRun, revalidateSignal, onNotify, isMobile }) {
  const { colors } = useTheme();
  const [input, setInput] = useState(JSON.stringify(SAMPLE_DATA[type], null, 2));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoFixCandidate, setAutoFixCandidate] = useState(null);
  const [tab, setTab] = useState("errors");
  const [registered, setRegistered] = useState(false);
  const [registering, setRegistering] = useState(false);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    setAutoFixCandidate(null);
    onNotify && onNotify(`Started validation for ${type}...`, 'info');
    try {
      const parsedCheck = tryParseJSON(input);
      if (!parsedCheck.ok) {
        // attempt auto-fix
        const fix = autoFixJSON(input);
        if (fix) {
          setAutoFixCandidate(fix);
          setError(`Invalid JSON: ${parsedCheck.message}. Try auto-fix.`);
        } else {
          setError(`Invalid JSON: ${parsedCheck.message}`);
        }
        return;
      }
      const parsed = parsedCheck.value;
      const body = type === "Patient"
        ? { data: parsed, resource_type: type }
        : { data: parsed, resource_type: type };

      const res = await fetch(API_BASE + ENDPOINTS[type], {
        method: "POST",
        headers: getApiHeaders(),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setResult(data);
      onNotify && onNotify(`Validation complete for ${type}`, 'success');
      if (onRun) onRun(type, true);
      setTab("errors");
    } catch (e) {
      setError(e.message);
      onNotify && onNotify(`Validation failed for ${type}: ${e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  }

  function prettyFormat() {
    setError(null);
    const parsed = tryParseJSON(input);
    if (!parsed.ok) {
      setError(`Cannot pretty-format: ${parsed.message}`);
      return;
    }
    setInput(JSON.stringify(parsed.value, null, 2));
    onNotify && onNotify('Formatted JSON', 'success');
  }

  async function registerPatient() {
    if (registering) return;

    setRegistering(true);
    onNotify && onNotify("Registering patient...", "info");

    try {
      const parsed = JSON.parse(input);
      const resource = result?.fixed_resource || result?.fhir_resource || parsed;
      const res = await fetch(API_BASE + "/patient/register", {
        method: "POST",
        headers: getApiHeaders(),
        body: JSON.stringify({ resource }),
      });
      const data = await res.json();

      if (!res.ok || !data.registered) {
        const detail = data?.message || data?.detail || "Patient registration failed.";
        onNotify && onNotify(detail, "error");
        return;
      }

      setRegistered(true);
      onNotify && onNotify("Patient registered successfully", "success");
      setTimeout(() => setRegistered(false), 3000);
    } catch (e) {
      console.error(e);
      onNotify && onNotify(e.message || "Could not register patient", "error");
    } finally {
      setRegistering(false);
    }
  }

  const hasMounted = useRef(false);

  // Run when global revalidate signal increments
  useEffect(() => {
    if (!hasMounted.current) {
      hasMounted.current = true;
      return;
    }
    if (typeof revalidateSignal === 'number' && revalidateSignal > 0) {
      run();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revalidateSignal]);

  const quality = result?.quality;
  const errors = result?.validation?.errors || result?.errors || [];
  const warnings = result?.validation?.warnings || result?.warnings || [];
  const mappingRules = result?.mapping?.applied_rules || result?.applied_rules || [];
  const unmapped = result?.mapping?.unmapped_fields || result?.unmapped_fields || [];
  const fhirResource = result?.fixed_resource || result?.fhir_resource || result?.mapped_resource;
  const lookup = result?.loinc_lookup || result?.snomed_lookup || result?.rxnorm_lookup;

  const TABS = [
    { id: "errors", label: `Errors (${errors.length})` },
    { id: "warnings", label: `Warnings (${warnings.length})` },
    { id: "mapping", label: `Mapping (${mappingRules.length})` },
    { id: "resource", label: "FHIR Output" },
  ];

  if (lookup) {
    const lookupLabel = result?.loinc_lookup ? "LOINC" : result?.snomed_lookup ? "SNOMED" : "RxNorm";
    TABS.splice(3, 0, { id: "lookup", label: lookupLabel });
  }

  return (
    <div style={{ display: isMobile ? "block" : "flex", gap: isMobile ? 16 : 20, height: "100%" }}>
      {/* Left: Input */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ color: colors.textDim, fontSize: 12, letterSpacing: "0.08em", fontWeight: 600 }}>
          RAW INPUT
        </div>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          style={{
            height: isMobile ? 300 : 400, background: colors.bg, border: `1px solid ${colors.border}`,
            borderRadius: 8, padding: isMobile ? 12 : 16, color: colors.text,
            fontFamily: "monospace", fontSize: isMobile ? 11 : 12, lineHeight: 1.6,
            resize: "none", outline: "none",
            boxShadow: `0 2px 8px ${colors.shadow}`,
            transition: "all 0.3s ease",
          }}
        />
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {result ? (
            <>
              <button style={{
                flex: isMobile ? "1 1 100%" : 1, background: colors.success, color: "#000", border: "none",
                borderRadius: 8, padding: "10px 0", fontWeight: 700, fontSize: 14,
                transition: "all 0.3s ease",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              }}>✓ Done</button>
              <div style={{display: 'inline-flex', gap: 8, flex: 1}}>
                <button onClick={run} disabled={loading} style={{
                  background: colors.surface, color: colors.text, border: `1px solid ${colors.border}`,
                  borderRadius: 8, padding: "10px 16px", fontWeight: 600, cursor: loading ? "wait" : "pointer",
                  transition: "all 0.3s ease",
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                  flex: 1,
                }}>{loading ? "Processing..." : "Re-run"}</button>
                <button onClick={prettyFormat} style={{
                  background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                  borderRadius: 8, padding: "10px 12px", fontWeight: 600, cursor: 'pointer',
                  transition: "all 0.3s ease",
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                  flex: 1,
                }}>Pretty format</button>
              </div>
            </>
          ) : (
            <>
              <button onClick={run} disabled={loading} style={{
                flex: 1, background: loading ? colors.accentDim : colors.accent,
                color: "#fff", border: "none", borderRadius: 8,
                padding: "10px 0", fontWeight: 600, cursor: loading ? "wait" : "pointer",
                fontSize: 14, transition: "all 0.3s ease",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              }}>
                {loading ? "Processing..." : `Validate ${type}`}
              </button>
              <button onClick={prettyFormat} style={{
                background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}`,
                borderRadius: 8, padding: "10px 12px", fontWeight: 600, cursor: 'pointer',
                transition: "all 0.3s ease",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                flex: 1,
              }}>Pretty format</button>
            </>
          )}
          {type === "Patient" && result && (
            <button onClick={registerPatient} disabled={registering} style={{
              background: registering ? colors.accentDim : registered ? colors.success : colors.surface,
              color: registered ? "#000" : colors.text,
              border: `1px solid ${registered ? colors.success : colors.border}`,
              borderRadius: 8, padding: "10px 16px",
              fontWeight: 600, cursor: registering ? "wait" : "pointer", fontSize: 14,
              transition: "all 0.3s ease",
              opacity: registering ? 0.9 : 1,
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
              flex: 1,
            }}>
              {registering ? "Registering..." : registered ? "✓ Registered" : "Register Patient"}
            </button>
          )}
        </div>
        {error && (
          <div style={{
            background: colors.error + "22", border: `1px solid ${colors.error}44`,
            borderRadius: 8, padding: 12, color: colors.error, fontSize: 13,
            boxShadow: `0 2px 8px ${colors.shadow}`,
            transition: "all 0.3s ease",
          }}>
            {error.includes("fetch") ? "Cannot connect to API. Make sure FastAPI is running on port 8000." : error}
            {autoFixCandidate && (
              <div style={{ marginTop: 8 }}>
                <button onClick={() => { setInput(autoFixCandidate); setAutoFixCandidate(null); setError(null); onNotify && onNotify('Applied JSON auto-fix', 'success'); }} style={{
                  background: colors.accent, color: "#fff", border: "none", padding: "6px 10px",
                  borderRadius: 6, cursor: "pointer", fontWeight: 700,
                  transition: "all 0.2s ease",
                }}>Auto-fix JSON</button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right: Results */}
      <div style={{ flex: isMobile ? "none" : 1.2, display: "flex", flexDirection: "column", gap: 12, marginTop: isMobile ? 16 : 0 }}>
        {result ? (
          <>
            {/* Quality + Stats */}
            <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
              <GradeRing grade={quality?.grade || "—"} colors={colors} />
              <div style={{ display: "flex", gap: 8, flex: 1, flexWrap: "wrap" }}>
                <Pill label="Errors Found" value={quality?.total_errors_found ?? errors.length} color={colors.error} colors={colors} />
                <Pill label="Auto-Fixed" value={quality?.errors_auto_fixed ?? 0} color={colors.success} colors={colors} />
                <Pill label="Remaining" value={quality?.remaining_errors ?? 0} color={quality?.remaining_errors > 0 ? colors.warning : colors.success} colors={colors} />
                <Pill label="Score" value={`${quality?.score ?? 0}%`} color={colors.accent} colors={colors} />
              </div>
            </div>

            {/* Status bar */}
            <div style={{
              display: "flex", gap: 8, alignItems: "center",
              background: colors.bg, border: `1px solid ${colors.border}`,
              borderRadius: 8, padding: "8px 14px",
              boxShadow: `0 2px 8px ${colors.shadow}`,
              transition: "all 0.3s ease",
            }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: (result?.validation?.final_valid || result?.valid)
                  ? colors.success : colors.error,
              }} />
              <span style={{ color: colors.textDim, fontSize: 13 }}>
                {(result?.validation?.final_valid || result?.valid)
                  ? "Resource is valid after fixes"
                  : `${errors.filter(e => !e.fix).length} error(s) require manual review`}
              </span>
              {unmapped.length > 0 && (
                <Badge color={colors.warning} colors={colors}>{unmapped.length} unmapped</Badge>
              )}
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: 4, borderBottom: `1px solid ${colors.border}`, overflowX: "auto" }}>
              {TABS.map(t => (
                <button key={t.id} onClick={() => setTab(t.id)} style={{
                  background: "none", border: "none",
                  borderBottom: tab === t.id ? `2px solid ${colors.accent}` : "2px solid transparent",
                  color: tab === t.id ? colors.accent : colors.muted,
                  padding: "8px 14px", cursor: "pointer", fontSize: 13,
                  fontWeight: tab === t.id ? 600 : 400, marginBottom: -1,
                  transition: "all 0.2s ease",
                  whiteSpace: "nowrap",
                }}>{t.label}</button>
              ))}
            </div>

            {/* Tab content */}
            <div style={{ flex: 1, overflowY: "auto", maxHeight: isMobile ? 400 : "auto" }}>
              {tab === "errors" && (
                errors.length === 0
                  ? <div style={{ color: colors.success, padding: 20, textAlign: "center" }}>✓ No errors found</div>
                  : errors.map((e, i) => <ErrorCard key={i} err={e} colors={colors} />)
              )}
              {tab === "warnings" && (
                warnings.length === 0
                  ? <div style={{ color: colors.muted, padding: 20, textAlign: "center" }}>No warnings</div>
                  : warnings.map((w, i) => <WarningCard key={i} w={w} colors={colors} />)
              )}
              {tab === "mapping" && (
                <div>
                  {mappingRules.map((r, i) => <MappingRow key={i} rule={r} colors={colors} />)}
                  {unmapped.length > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <div style={{ color: colors.warning, fontSize: 12, marginBottom: 8, fontWeight: 600 }}>
                        UNMAPPED FIELDS
                      </div>
                      {unmapped.map((u, i) => (
                        <div key={i} style={{
                          display: "flex", justifyContent: "space-between",
                          padding: "6px 0", borderBottom: `1px solid ${colors.border}`,
                          fontFamily: "monospace", fontSize: 12,
                          transition: "all 0.2s ease",
                        }}>
                          <span style={{ color: colors.warning }}>{renderValue(u.field)}</span>
                          <span style={{ color: colors.muted, whiteSpace: "pre-wrap", textAlign: "right" }}>{renderValue(u.value)}</span>
                          <Badge color={colors.warning} colors={colors}>unmapped</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {tab === "lookup" && lookup && (
                <div style={{
                  background: colors.bg, border: `1px solid ${colors.border}`,
                  borderRadius: 8, padding: 16,
                  boxShadow: `0 2px 8px ${colors.shadow}`,
                  transition: "all 0.3s ease",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                    <Badge color={lookup.found ? colors.success : colors.error} colors={colors}>
                      {lookup.found ? "found" : "not found"}
                    </Badge>
                    <Badge color={colors.accent} colors={colors}>{renderValue(lookup.source)}</Badge>
                  </div>
                  {lookup.found && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                      <div>
                        <div style={{ color: colors.muted, fontSize: 11, marginBottom: 2 }}>CODE</div>
                        <div style={{ color: colors.accent, fontFamily: "monospace", fontSize: 16, fontWeight: 700 }}>
                          {renderValue(lookup.code)}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: colors.muted, fontSize: 11, marginBottom: 2 }}>DISPLAY</div>
                        <div style={{ color: colors.text, fontSize: 14 }}>{renderValue(lookup.display)}</div>
                      </div>
                      <div>
                        <div style={{ color: colors.muted, fontSize: 11, marginBottom: 2 }}>SYSTEM</div>
                        <div style={{ color: colors.textDim, fontSize: 12, fontFamily: "monospace" }}>
                          {renderValue(lookup.system)}
                        </div>
                      </div>
                      {lookup.class && (
                        <div>
                          <div style={{ color: colors.muted, fontSize: 11, marginBottom: 2 }}>CLASS</div>
                          <Badge color={colors.accent} colors={colors}>{renderValue(lookup.class)}</Badge>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              {tab === "resource" && fhirResource && <JsonBlock data={fhirResource} resourceType={type} colors={colors} />}
            </div>
          </>
        ) : (
          <ResultsBlankState colors={colors} />
        )}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────
function FhirResourcesContent() {
  const { colors, toggleTheme, theme } = useTheme();
  const navigate = useNavigate();

  const RESOURCES = ["Patient", "Observation", "Condition", "Encounter", "MedicationRequest", "Bundle"];
  const [activeResource, setActiveResource] = useState("Patient");
  const [runStatus, setRunStatus] = useState({});
  const [revalidateSignal, setRevalidateSignal] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isMobile, setIsMobile] = useState(false);
  const notificationDuration = 4000;

  useEffect(() => {
    if (revalidateSignal > 0) {
      const resetId = setTimeout(() => setRevalidateSignal(0), 10);
      return () => clearTimeout(resetId);
    }
  }, [revalidateSignal]);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  function notify(message, type = "info", durationMs) {
    const id = Date.now() + Math.random();
    setNotifications(prev => [...prev, { id, message, type }]);
    const timeout = typeof durationMs === "number" ? durationMs : notificationDuration;
    if (timeout && timeout > 0) {
      setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), timeout);
    }
  }

  function removeNotification(id) {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }

  function logout() {
    localStorage.removeItem("smartfhirApiKey");
    localStorage.removeItem("smartfhirEmail");
    localStorage.removeItem("smartfhirPlan");
    localStorage.removeItem("smartfhirUsage");
    localStorage.removeItem("smartfhirLimit");
    localStorage.removeItem("smartfhirRemaining");
    localStorage.removeItem("smartfhirLastUsed");
    notify("Logged out successfully", "success");
    navigate("/");
  }

  return (
    <div style={{
      minHeight: "100vh", background: colors.bg, color: colors.text,
      fontFamily: "'Inter', system-ui, sans-serif",
      transition: "background 0.3s ease, color 0.3s ease",
    }}>
      <div style={{
        position: "sticky", top: 0, zIndex: 20,
        background: colors.surface, borderBottom: `1px solid ${colors.border}`,
        padding: isMobile ? "14px 16px" : "14px 24px",
        display: "flex", flexDirection: isMobile ? "column" : "row",
        alignItems: isMobile ? "stretch" : "center",
        justifyContent: "space-between", gap: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: isMobile ? 16 : 18 }}>FHIR Resources</div>
            <div style={{ color: colors.textDim, fontSize: isMobile ? 12 : 13, marginTop: 2 }}>
              Map and validate your FHIR resources with the built-in pipeline.
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <button onClick={toggleTheme} aria-label="Toggle Theme" style={{
            width: 34, height: 34, borderRadius: 10, border: `1px solid ${colors.border}`,
            display: "grid", placeItems: "center", background: "transparent", color: colors.text,
            cursor: "pointer", transition: "all 0.2s"
          }}>
            {theme === "dark" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
            )}
          </button>
          <button
            onClick={() => {
              notify("Revalidating all resources…", "info");
              setRevalidateSignal(s => s + 1);
            }}
            style={{
              border: `1px solid ${colors.accent}`, background: colors.accentDim, color: colors.accent,
              borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = colors.accent + "33"}
            onMouseLeave={(e) => e.currentTarget.style.background = colors.accentDim}
          >
            ↻ Revalidate All
          </button>
          <button onClick={() => navigate("/api-key")} style={{
            border: `1px solid ${colors.border}`, background: "transparent", color: colors.text,
            borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
          }} onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)"} onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
            Manage API
          </button>
          <button onClick={() => navigate("/tools")} style={{
            border: `1px solid ${colors.border}`, background: "transparent", color: colors.text,
            borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
          }} onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)"} onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
            Back to tools
          </button>
          <button onClick={logout} style={{
            border: "1px solid #ef4444", background: "transparent", color: "#ef4444",
            borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
          }} onMouseEnter={(e) => e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)"} onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
            Logout
          </button>
        </div>
      </div>

      <div style={{
        borderBottom: `1px solid ${colors.border}`,
        padding: isMobile ? "12px 16px" : "16px 24px",
        background: colors.surface,
        display: "grid", gap: 12,
      }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {RESOURCES.map(r => (
            <button key={r} onClick={() => setActiveResource(r)} style={{
              background: activeResource === r ? colors.accentDim : colors.bg,
              border: activeResource === r ? `1px solid ${colors.accent}44` : `1px solid ${colors.border}`,
              color: activeResource === r ? colors.accent : colors.muted,
              borderRadius: 8, padding: "8px 12px", cursor: "pointer",
              fontSize: 13, fontWeight: activeResource === r ? 700 : 500,
            }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                <span>{r}</span>
                {runStatus[r] && (
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: colors.success, display: "inline-block" }} />
                )}
              </span>
            </button>
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
          {WORKFLOW_STEPS.map((step, index) => (
            <div key={step.title} style={{
              flex: isMobile ? "1 1 100%" : "1 1 140px",
              minWidth: isMobile ? "auto" : 140,
              background: colors.bg, border: `1px solid ${colors.border}`,
              borderRadius: 8, padding: isMobile ? "8px 10px" : "10px 12px",
              boxShadow: `0 2px 6px ${colors.shadow}`,
            }}>
              <div style={{ color: colors.accent, fontSize: isMobile ? 9 : 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>
                {`Step ${index + 1}`}
              </div>
              <div style={{ color: colors.text, fontSize: isMobile ? 12 : 13, fontWeight: 700, marginBottom: 4 }}>
                {step.title}
              </div>
              <div style={{ color: colors.textDim, fontSize: isMobile ? 10 : 11, lineHeight: 1.4 }}>
                {step.subtitle}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: isMobile ? "12px 16px 24px" : "24px" }}>
        {RESOURCES.map(r => (
          <div key={r} style={{ display: activeResource === r ? "block" : "none" }}>
            {r === "Bundle" ? (
              <BundlePanel onNotify={notify} isMobile={isMobile} />
            ) : (
              <ResourcePanel
                type={r}
                onRun={(resName, has) => setRunStatus(prev => ({ ...prev, [resName]: has }))}
                revalidateSignal={revalidateSignal}
                onNotify={notify}
                isMobile={isMobile}
              />
            )}
          </div>
        ))}
        <Notifications items={notifications} remove={removeNotification} />
      </div>
    </div>
  );
}

export default function FhirResourcesPage() {
  return (
    <ThemeProvider>
      <FhirResourcesContent />
    </ThemeProvider>
  );
}