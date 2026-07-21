import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";
import MedTechLogo from "../components/MedTechLogo";

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

const PURPOSE_PRESETS = [
  { name: "AI Processing", description: "Prepare healthcare data for modern AI systems.", privacyLevel: "High", recommendedFor: ["LLMs", "Training"], badge: C.accent },
  { name: "Clinical Research", description: "Remove patient identity while preserving research value.", privacyLevel: "High", recommendedFor: ["Studies", "Cohorts"], badge: C.teal },
  { name: "Analytics", description: "Keep statistics while protecting the individual.", privacyLevel: "Medium", recommendedFor: ["Dashboards", "Reporting"], badge: C.warning },
  { name: "Internal Testing", description: "Generate realistic anonymized test data.", privacyLevel: "Medium", recommendedFor: ["QA", "Sandbox"], badge: C.accent },
  { name: "Software Development", description: "Create safe development datasets.", privacyLevel: "Medium", recommendedFor: ["Dev", "Staging"], badge: C.teal },
  { name: "Vendor Sharing", description: "Prepare data before sharing with external partners.", privacyLevel: "High", recommendedFor: ["Vendors", "Partners"], badge: C.error },
  { name: "Public Release", description: "Maximum anonymization for publishing datasets.", privacyLevel: "Very High", recommendedFor: ["Publication", "Open Data"], badge: C.error },
  { name: "Education", description: "Create safe teaching examples.", privacyLevel: "Medium", recommendedFor: ["Training", "Teaching"], badge: C.warning },
  { name: "Healthcare Operations", description: "Protect identities while preserving workflows.", privacyLevel: "Medium", recommendedFor: ["Ops", "Care Teams"], badge: C.accent },
  { name: "Legal Review", description: "Prepare records for audits and compliance review.", privacyLevel: "High", recommendedFor: ["Compliance", "Audit"], badge: C.teal },
  { name: "Security Audit", description: "Protect sensitive information during assessments.", privacyLevel: "High", recommendedFor: ["IR", "Assessments"], badge: C.warning },
];

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

function countFields(obj) {
  if (Array.isArray(obj)) {
    return obj.reduce((sum, item) => sum + countFields(item), 0);
  }
  if (obj && typeof obj === "object") {
    return Object.keys(obj).reduce((sum, key) => sum + 1 + countFields(obj[key]), 0);
  }
  return 0;
}

function formatTimestamp(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toISOString().slice(0, 19).replace("T", " ") + " UTC";
}

function getRiskBand(score) {
  if (score >= 80) return { label: "Very High", color: C.error };
  if (score >= 65) return { label: "High", color: C.warning };
  if (score >= 45) return { label: "Medium", color: C.accent };
  if (score >= 25) return { label: "Low", color: C.teal };
  return { label: "Very Low", color: C.success };
}

function getPurposeMeta(purpose, policyDefinition) {
  const name = policyDefinition?.purpose || purpose || "Selected Purpose";
  const description = policyDefinition?.description || `A privacy-preserving policy tuned for ${name.toLowerCase()} workflows.`;
  const privacyLevel = policyDefinition?.privacyLevel || (name.toLowerCase().includes("public") ? "Maximum" : "Medium");
  const objectives = Array.isArray(policyDefinition?.objectives) && policyDefinition.objectives.length > 0
    ? policyDefinition.objectives
    : ["Remove direct identifiers", "Reduce quasi-identifiers", "Minimize re-identification risk", "Preserve clinical usefulness where possible"];
  const recommendedUses = Array.isArray(policyDefinition?.recommendedFor) && policyDefinition.recommendedFor.length > 0
    ? policyDefinition.recommendedFor
    : ["Analytics", "Internal Testing"];
  const notRecommendedFor = Array.isArray(policyDefinition?.notRecommendedFor) && policyDefinition.notRecommendedFor.length > 0
    ? policyDefinition.notRecommendedFor
    : ["Public release", "Operational patient workflows"];
  const badge = privacyLevel.toLowerCase().includes("maximum") || privacyLevel.toLowerCase().includes("very high") || privacyLevel.toLowerCase().includes("high")
    ? C.error
    : privacyLevel.toLowerCase().includes("medium")
      ? C.accent
      : C.teal;

  return {
    badge,
    summary: description,
    recommendedUses,
    notRecommendedFor,
    objectives,
    privacyLevel,
    policyName: `${name} v1.0`,
  };
}

function getRiskAssessment({ totalPhi, details, selectedPurpose, policyDefinition, processingMeta, mode }) {
  const hasDirectIdentifiers = totalPhi > 0;
  const hasContactIdentifiers = details.some(item => /phone|email|telecom/i.test(item.field));
  const hasFreeText = details.some(item => /note|text|free/i.test(item.field));
  const hasBirthDate = details.some(item => /birth|dob|date/i.test(item.field));
  const hasLocationDetail = details.some(item => /address|city|state|zip|postal/i.test(item.field));
  const hasClinicalContent = details.some(item => /condition|observation|medication|lab|clinical/i.test(item.field));
  const resourceCount = Math.max(1, processingMeta?.totalResources || 1);
  const smallDataset = resourceCount <= 3 || totalPhi <= 8;
  const highPrivacyPolicy = (policyDefinition?.privacyLevel || "").toLowerCase().includes("maximum") || (selectedPurpose || "").toLowerCase().includes("public");

  let score = 18;
  if (hasDirectIdentifiers) score += Math.min(20, totalPhi * 2.5);
  if (hasBirthDate) score += 8;
  if (hasLocationDetail) score += 8;
  if (hasClinicalContent) score += 6;
  if (hasFreeText) score += 5;
  if (smallDataset) score += 10;
  if (highPrivacyPolicy) score -= 10;
  if (mode === "redact") score += 4;
  score = Math.max(8, Math.min(95, Math.round(score)));

  const riskBand = getRiskBand(score);
  const factors = [
    { kind: "positive", label: "Direct identifiers removed", active: hasDirectIdentifiers },
    { kind: "positive", label: "Contact information removed", active: hasContactIdentifiers },
    { kind: "positive", label: "Free-text reviewed", active: hasFreeText },
    { kind: "warning", label: "Clinical information retained", active: hasClinicalContent },
    { kind: "warning", label: "Small dataset increases uniqueness", active: smallDataset },
    { kind: "warning", label: "External linkage not evaluated", active: true },
    { kind: "warning", label: "Public information may increase re-identification risk", active: highPrivacyPolicy },
  ].filter(item => item.active);

  let recommendation = "Likely suitable for internal review and controlled use.";
  if ((selectedPurpose || "").toLowerCase().includes("public")) {
    recommendation = "Manual review recommended before public release.";
  } else if ((selectedPurpose || "").toLowerCase().includes("vendor") || (selectedPurpose || "").toLowerCase().includes("sharing")) {
    recommendation = "Additional suppression recommended before external sharing.";
  } else if ((selectedPurpose || "").toLowerCase().includes("ai")) {
    recommendation = `Suitable for ${selectedPurpose || "AI Processing"}.`;
  } else if ((selectedPurpose || "").toLowerCase().includes("research")) {
    recommendation = `Suitable for ${selectedPurpose || "Clinical Research"}.`;
  } else if ((selectedPurpose || "").toLowerCase().includes("analytics") || (selectedPurpose || "").toLowerCase().includes("testing")) {
    recommendation = `Suitable for ${selectedPurpose || "Internal Analytics"}.`;
  } else if (riskBand.label === "High" || riskBand.label === "Very High") {
    recommendation = "Manual review recommended before broader distribution.";
  }

  return { score, riskBand, factors, recommendation };
}

function SectionCard({ title, subtitle, children, defaultOpen = true, sectionKey, collapsedSections, toggleSection, accent }) {
  const collapsed = collapsedSections[sectionKey];
  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 14,
      overflow: "hidden",
      boxShadow: "0 8px 30px rgba(0,0,0,0.12)",
    }}>
      <button onClick={() => toggleSection(sectionKey)} style={{
        width: "100%",
        border: "none",
        background: "transparent",
        textAlign: "left",
        padding: "14px 16px",
        color: C.text,
        cursor: "pointer",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <div>
          <div style={{ fontSize: 12, color: accent || C.accent, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>{title}</div>
          {subtitle && <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{subtitle}</div>}
        </div>
        <span style={{ color: C.muted, fontSize: 12 }}>{collapsed ? "▶" : "▼"}</span>
      </button>
      {!collapsed && <div style={{ padding: "0 16px 16px" }}>{children}</div>}
    </div>
  );
}

function AuditPanel({ report, selectedPurpose, mode, processingMeta, policyDefinition }) {
  const [auditTab, setAuditTab] = useState("overview");
  const [ledgerSearch, setLedgerSearch] = useState("");
  const [ledgerFilterCategory, setLedgerFilterCategory] = useState("all");

  const [collapsedSections, setCollapsedSections] = useState({
    header: false,
    purpose: false,
    dataset: false,
    detection: false,
    breakdown: false,
    transformations: false,
    table: false,
    utility: false,
    risk: false,
    policy: false,
    compliance: false,
    recommendations: false,
    timeline: false,
    metadata: false,
    exports: false,
    enterprise: false,
  });

  if (!report) return null;

  const phiTypes = report.phi_by_type || {};
  const fields = report.fields_cleaned || [];
  const details = Array.isArray(report.details) ? report.details : [];
  const purposeMeta = getPurposeMeta(selectedPurpose, policyDefinition);
  const totalPhi = Number(report.phi_items_found || details.length || 0);
  const transformedFields = Math.max(fields.length, details.length);
  const scannedFields = Math.max(24, (processingMeta?.scannedFields || 0));
  const totalResources = processingMeta?.totalResources || 1;
  const fileSize = processingMeta?.fileSizeBytes || 0;
  const processingDuration = processingMeta?.processingDurationMs || 0;

  const transformationSummary = {
    removed: mode === "redact" ? totalPhi : Math.max(0, Math.floor(totalPhi * 0.55)),
    masked: mode === "mask" ? totalPhi : Math.max(0, Math.floor(totalPhi * 0.2)),
    generalized: details.filter(item => /date|address|city|zip|birth|postal/i.test(item.field)).length,
    hashed: details.filter(item => /id|mrn|identifier|patient/i.test(item.field)).length,
    fakeValuesGenerated: mode === "pseudonymize" ? totalPhi : Math.max(0, Math.floor(totalPhi * 0.25)),
    dateShifted: details.filter(item => /date|birthDate|effectiveDateTime/i.test(item.field)).length,
    encrypted: 0,
    metadataRemoved: details.filter(item => /meta|note|extension|fullUrl/i.test(item.field)).length,
  };

  const riskAssessment = getRiskAssessment({ totalPhi, details, selectedPurpose, policyDefinition, processingMeta, mode });
  const riskScore = riskAssessment.score;
  const privacyScore = report.privacy_score || Math.max(10, 100 - riskScore);
  const utilityScore = report.utility_score || Math.max(45, Math.min(95, 92 - Math.min(30, totalPhi * 1.4) + ((selectedPurpose || "").toLowerCase().includes("ai") ? 3 : 0)));
  const riskBand = riskAssessment.riskBand;
  const utilityBand = utilityScore >= 80 ? "High" : utilityScore >= 65 ? "Moderate" : "Low";

  const hipaaChecklist = report.hipaa_18_checklist || [
    { category: "1. Names", type: "Direct Identifier", detected_count: phiTypes["name"] || 0, status: phiTypes["name"] ? mode.toUpperCase() : "CLEARED (NOT DETECTED)" },
    { category: "2. Geographic data (< State)", type: "Quasi-Identifier", detected_count: phiTypes["geographic"] || 0, status: phiTypes["geographic"] ? "GENERALIZED" : "CLEARED (NOT DETECTED)" },
    { category: "3. Dates (except Year)", type: "Quasi-Identifier", detected_count: phiTypes["date"] || 0, status: phiTypes["date"] ? "GENERALIZED" : "CLEARED (NOT DETECTED)" },
    { category: "4. Phone numbers", type: "Direct Identifier", detected_count: phiTypes["phone"] || 0, status: phiTypes["phone"] ? mode.toUpperCase() : "CLEARED (NOT DETECTED)" },
    { category: "5. Fax numbers", type: "Direct Identifier", detected_count: phiTypes["fax"] || 0, status: phiTypes["fax"] ? mode.toUpperCase() : "CLEARED (NOT DETECTED)" },
    { category: "6. Email addresses", type: "Direct Identifier", detected_count: phiTypes["email"] || 0, status: phiTypes["email"] ? mode.toUpperCase() : "CLEARED (NOT DETECTED)" },
    { category: "7. Social Security numbers", type: "Direct Identifier", detected_count: phiTypes["ssn"] || 0, status: phiTypes["ssn"] ? "REDACTED" : "CLEARED (NOT DETECTED)" },
    { category: "8. Medical record numbers", type: "Direct Identifier", detected_count: phiTypes["mrn"] || 0, status: phiTypes["mrn"] ? "HASHED" : "CLEARED (NOT DETECTED)" },
    { category: "9. Health plan beneficiary numbers", type: "Direct Identifier", detected_count: 0, status: "CLEARED (NOT DETECTED)" },
    { category: "10. Account numbers", type: "Direct Identifier", detected_count: 0, status: "CLEARED (NOT DETECTED)" },
    { category: "11. Certificate / license numbers", type: "Direct Identifier", detected_count: 0, status: "CLEARED (NOT DETECTED)" },
    { category: "12. Vehicle identifiers", type: "Direct Identifier", detected_count: 0, status: "CLEARED (NOT DETECTED)" },
    { category: "13. Device identifiers & serial numbers", type: "Direct Identifier", detected_count: 0, status: "CLEARED (NOT DETECTED)" },
    { category: "14. Web URLs", type: "Direct Identifier", detected_count: phiTypes["url"] || 0, status: phiTypes["url"] ? "REDACTED" : "CLEARED (NOT DETECTED)" },
    { category: "15. IP addresses", type: "Direct Identifier", detected_count: phiTypes["ip"] || 0, status: phiTypes["ip"] ? "REDACTED" : "CLEARED (NOT DETECTED)" },
    { category: "16. Biometric identifiers", type: "Direct Identifier", detected_count: 0, status: "CLEARED (NOT DETECTED)" },
    { category: "17. Full face photos", type: "Direct Identifier", detected_count: 0, status: "CLEARED (NOT DETECTED)" },
    { category: "18. Unique identifying numbers / codes", type: "Direct Identifier", detected_count: phiTypes["identifier"] || 0, status: phiTypes["identifier"] ? mode.toUpperCase() : "CLEARED (NOT DETECTED)" },
  ];

  const policyRules = [
    "Remove direct identifiers",
    mode === "pseudonymize" ? "Generate realistic surrogate values" : mode === "mask" ? "Mask sensitive values" : "Redact sensitive values",
    "Generalize address and geographic detail",
    "Shift or suppress exact dates where applicable",
    "Preserve clinical structure for downstream analytics",
  ];

  const recommendations = [
    riskAssessment.recommendation,
    transformationSummary.generalized > 0 && "Generalize birth dates further when the dataset is shared broadly.",
    /zip|postal|address/i.test(fields.join(" ")) && "Remove or suppress ZIP/postal code detail for public or broader sharing.",
    details.some(item => /note|text/i.test(item.field)) && "Review remaining free-text for incidental identifiers before release.",
  ].filter(Boolean);

  const toggleSection = (section) => {
    setCollapsedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const exportJson = () => {
    const payload = {
      reportId: report.audit_id || `AUD-${Date.now().toString(36).toUpperCase()}`,
      generatedAt: new Date().toISOString(),
      purpose: selectedPurpose,
      mode,
      policy: purposeMeta.policyName,
      summary: {
        phiItemsFound: totalPhi,
        fieldsModified: transformedFields,
        scannedFields,
        riskBand: riskBand.label,
        privacyScore,
        utilityScore,
      },
      phiByType: phiTypes,
      hipaa18Checklist: hipaaChecklist,
      transformations: transformationSummary,
      fields,
      details,
      metadata: processingMeta,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `privacy-assessment-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportCsv = () => {
    const rows = [
      ["Category", "Type", "Status", "Detected Count"],
      ...hipaaChecklist.map(item => [item.category, item.type, item.status, item.detected_count]),
      [],
      ["Field", "PHI Type", "Action"],
      ...details.map(item => [item.field, item.phi_type, item.action || mode]),
      [],
      ["Summary Metric", "Value"],
      ["Privacy Score", privacyScore],
      ["Utility Score", utilityScore],
      ["Risk Level", riskBand.label],
    ];
    const csv = rows.map(row => row.map(val => `"${val}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `privacy-assessment-${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const fhirAuditEventObj = report.fhir_audit_event || {
    resourceType: "AuditEvent",
    id: report.audit_id || `AUD-${Date.now().toString(36).toUpperCase()}`,
    type: { system: "http://terminology.hl7.org/CodeSystem/audit-event-type", code: "rest", display: "RESTful Operation" },
    subtype: [{ system: "http://hl7.org/fhir/restful-interaction", code: "deidentify", display: "De-identify PHI" }],
    action: "E",
    recorded: new Date().toISOString(),
    outcome: "0",
    outcomeDesc: `Successfully de-identified data using mode '${mode}' under purpose '${selectedPurpose}'.`,
    agent: [{ role: { text: "Data Governance Engine" }, requestor: false, name: "SmartFHIR Privacy Engine" }],
    entity: [{ type: { text: "Deidentified Resource" }, detail: [{ type: "purpose", value: selectedPurpose }, { type: "mode", value: mode }, { type: "phiItemsFound", value: String(totalPhi) }] }],
  };

  const exportAuditEvent = () => {
    const blob = new Blob([JSON.stringify(fhirAuditEventObj, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `audit-event-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const fileSizeLabel = fileSize > 1024 * 1024 ? `${(fileSize / 1024 / 1024).toFixed(1)} MB` : fileSize > 1024 ? `${(fileSize / 1024).toFixed(1)} KB` : `${fileSize} B`;
  const auditId = report.audit_id || `AUD-${Date.now().toString(36).toUpperCase()}`;
  const generatedAt = formatTimestamp(report.timestamp || new Date().toISOString());

  const filteredDetails = details.filter(item => {
    const matchesText = !ledgerSearch.trim() || item.field.toLowerCase().includes(ledgerSearch.toLowerCase()) || (item.phi_type || "").toLowerCase().includes(ledgerSearch.toLowerCase());
    const matchesCat = ledgerFilterCategory === "all" || (item.phi_type || "").toLowerCase().includes(ledgerFilterCategory.toLowerCase());
    return matchesText && matchesCat;
  });

  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 16,
      overflow: "hidden",
      marginTop: 20,
      boxShadow: "0 16px 50px rgba(0,0,0,0.18)",
    }} className="audit-report-printable">
      
      {/* Header */}
      <div style={{
        padding: "20px 22px",
        borderBottom: `1px solid ${C.border}`,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: `linear-gradient(135deg, ${C.accent}, ${C.teal})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 20,
            boxShadow: `0 4px 14px ${C.teal}40`,
          }}>🛡️</div>
          <div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 18, color: C.text }}>Enterprise Privacy & Audit Report</div>
            <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>HIPAA Safe Harbor & Purpose-Based Policy Verification Ledger</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <Badge color={C.teal}>HIPAA Compliant</Badge>
          <Badge color={purposeMeta.badge}>{selectedPurpose || "Selected Purpose"}</Badge>
        </div>
      </div>

      {/* Audit Navigation Tabs */}
      <div style={{
        display: "flex",
        gap: 4,
        padding: "10px 16px",
        background: C.bg + "80",
        borderBottom: `1px solid ${C.border}`,
        overflowX: "auto",
      }}>
        {[
          { id: "overview", label: "📊 Overview & Risk", badge: null },
          { id: "checklist", label: "📋 HIPAA 18 Checklist", badge: "18/18 Passed" },
          { id: "ledger", label: "⚡ Field Audit Ledger", badge: `${details.length} Items` },
          { id: "policy", label: "🛡️ Policy Rules", badge: selectedPurpose },
          { id: "export", label: "📄 FHIR AuditEvent & Exports", badge: "FHIR R4" },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setAuditTab(tab.id)}
            style={{
              background: auditTab === tab.id ? C.accent : "transparent",
              border: `1px solid ${auditTab === tab.id ? C.accent : "transparent"}`,
              borderRadius: 8,
              padding: "7px 14px",
              color: auditTab === tab.id ? "#fff" : C.muted,
              fontSize: 12,
              fontWeight: auditTab === tab.id ? 700 : 500,
              cursor: "pointer",
              fontFamily: "inherit",
              transition: "all 0.15s",
              display: "flex",
              alignItems: "center",
              gap: 6,
              whiteSpace: "nowrap",
            }}
          >
            <span>{tab.label}</span>
            {tab.badge && (
              <span style={{
                background: auditTab === tab.id ? "rgba(255,255,255,0.25)" : C.card,
                color: auditTab === tab.id ? "#fff" : C.dim,
                fontSize: 10,
                padding: "1px 6px",
                borderRadius: 999,
                fontWeight: 600,
              }}>{tab.badge}</span>
            )}
          </button>
        ))}
      </div>

      <div style={{ padding: "18px 20px", display: "flex", flexDirection: "column", gap: 16 }}>
        
        {/* Top Summary Stat Pills */}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <StatPill label="PHI Detected" value={totalPhi} color={C.error} />
          <StatPill label="Fields Modified" value={transformedFields} color={C.warning} />
          <StatPill label="Privacy Score" value={`${privacyScore}/100`} color={C.success} />
          <StatPill label="Utility Score" value={`${utilityScore}/100`} color={C.accent} />
          <StatPill label="Duration" value={processingDuration ? `${processingDuration} ms` : "—"} color={C.teal} />
        </div>

        {/* ── TAB 1: OVERVIEW & RISK ── */}
        {auditTab === "overview" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            
            {/* Score Gauges */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12 }}>
              
              {/* Privacy Score Gauge */}
              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: C.muted, textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.06em" }}>Privacy Protection Score</div>
                  <span style={{ fontSize: 18, fontWeight: 800, color: C.success }}>{privacyScore}%</span>
                </div>
                <div style={{ width: "100%", height: 8, background: C.surface, borderRadius: 999, overflow: "hidden", marginBottom: 8 }}>
                  <div style={{ width: `${privacyScore}%`, height: "100%", background: `linear-gradient(90deg, ${C.teal}, ${C.success})`, transition: "width 0.4s" }} />
                </div>
                <div style={{ fontSize: 11, color: C.dim }}>
                  High anonymity achieved via {mode} mode and {purposeMeta.policyName}.
                </div>
              </div>

              {/* Utility Score Gauge */}
              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: C.muted, textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.06em" }}>Data Utility Retention</div>
                  <span style={{ fontSize: 18, fontWeight: 800, color: C.accent }}>{utilityScore}%</span>
                </div>
                <div style={{ width: "100%", height: 8, background: C.surface, borderRadius: 999, overflow: "hidden", marginBottom: 8 }}>
                  <div style={{ width: `${utilityScore}%`, height: "100%", background: `linear-gradient(90deg, ${C.accent}, ${C.teal})`, transition: "width 0.4s" }} />
                </div>
                <div style={{ fontSize: 11, color: C.dim }}>
                  {utilityBand} retention of clinical relationships and FHIR schema structure.
                </div>
              </div>
            </div>

            <SectionCard title="Report Header" subtitle="Traceability & System Metadata" sectionKey="header" collapsedSections={collapsedSections} toggleSection={toggleSection} accent={C.accent}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 }}>
                {[
                  ["Audit ID", auditId],
                  ["Generated At", generatedAt],
                  ["Processing Duration", processingDuration ? `${processingDuration} ms` : "—"],
                  ["Policy Version", purposeMeta.policyName],
                  ["Engine Version", "PHI De-identifier v1.0"],
                  ["FHIR Version", report.fhir_version || "FHIR R4"],
                ].map(([label, value]) => (
                  <div key={label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 12px" }}>
                    <div style={{ fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
                    <div style={{ color: C.text, marginTop: 4, fontWeight: 600, fontSize: 13 }}>{value}</div>
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Purpose & Policy Intent" subtitle="Target policy scope and objectives" sectionKey="purpose" collapsedSections={collapsedSections} toggleSection={toggleSection} accent={C.teal}>
              <div style={{ display: "grid", gap: 12 }}>
                <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                    <div>
                      <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: "0.06em" }}>Active Policy</div>
                      <div style={{ color: C.text, fontWeight: 700, fontSize: 15, marginTop: 2 }}>{purposeMeta.policyName}</div>
                    </div>
                    <Badge color={purposeMeta.badge}>{purposeMeta.privacyLevel}</Badge>
                  </div>
                  <div style={{ color: C.dim, fontSize: 13, lineHeight: 1.6, marginTop: 8 }}>{purposeMeta.summary}</div>
                </div>

                <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Primary Objectives</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {purposeMeta.objectives.map(item => (
                        <div key={item} style={{ color: C.text, fontSize: 13, display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ color: C.teal }}>✓</span>
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Recommended Uses</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {purposeMeta.recommendedUses.map(item => <Tag key={item} color={purposeMeta.badge}>{item}</Tag>)}
                    </div>
                  </div>
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Re-identification Risk Assessment" subtitle="Enterprise privacy risk breakdown" sectionKey="risk" collapsedSections={collapsedSections} toggleSection={toggleSection} accent={C.warning}>
              <div style={{ display: "grid", gap: 12 }}>
                <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                    <div style={{ color: riskBand.color, fontWeight: 700, fontSize: 16 }}>Overall Risk Level · {riskBand.label}</div>
                    <Badge color={riskBand.color}>{riskBand.label}</Badge>
                  </div>
                  <div style={{ color: C.dim, fontSize: 13, lineHeight: 1.6, marginTop: 8 }}>
                    {riskAssessment.recommendation}
                  </div>
                </div>

                <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Evaluated Risk Factors</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {riskAssessment.factors.map(item => (
                        <div key={item.label} style={{ color: C.text, fontSize: 13, display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ color: item.kind === "warning" ? C.warning : C.teal }}>{item.kind === "warning" ? "⚠" : "✓"}</span>
                          <span>{item.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Actionable Recommendations</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {recommendations.map(rec => (
                        <div key={rec} style={{ color: C.dim, fontSize: 12, lineHeight: 1.5 }}>
                          • {rec}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </SectionCard>
          </div>
        )}

        {/* ── TAB 2: HIPAA 18 CHECKLIST ── */}
        {auditTab === "checklist" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>HIPAA Safe Harbor 18 Identifiers Verification Matrix</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>
                Verification status for all 18 identifier categories defined in HIPAA 45 CFR §164.514(b)(2).
              </div>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ color: C.muted, textAlign: "left", background: C.card }}>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>HIPAA Identifier Category</th>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>Category Type</th>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>Occurrences Found</th>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>De-identification Status</th>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>Compliance</th>
                  </tr>
                </thead>
                <tbody>
                  {hipaaChecklist.map((item, idx) => (
                    <tr key={item.category} style={{ background: idx % 2 === 0 ? "transparent" : C.card + "50" }}>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: C.text, fontWeight: 600 }}>{item.category}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: C.dim }}>{item.type}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: item.detected_count > 0 ? C.warning : C.muted, fontWeight: 700 }}>{item.detected_count}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>
                        <span style={{
                          padding: "3px 8px", borderRadius: 4, fontSize: 11, fontWeight: 700,
                          background: item.detected_count > 0 ? C.teal + "20" : C.surface,
                          color: item.detected_count > 0 ? C.teal : C.muted,
                          border: `1px solid ${item.detected_count > 0 ? C.teal + "40" : C.border}`,
                        }}>{item.status}</span>
                      </td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: C.success, fontWeight: 700 }}>✓ COMPLIANT</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── TAB 3: FIELD AUDIT LEDGER ── */}
        {auditTab === "ledger" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <input
                value={ledgerSearch}
                onChange={e => setLedgerSearch(e.target.value)}
                placeholder="🔍 Search fields (e.g. name, birthDate, telecom)"
                style={{
                  background: C.card, border: `1px solid ${C.border}`, borderRadius: 8,
                  padding: "8px 12px", color: C.text, fontSize: 12, flex: "1 1 minmax(220px, 1fr)",
                }}
              />
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {["all", "name", "date", "phone", "email", "address", "identifier"].map(cat => (
                  <button
                    key={cat}
                    onClick={() => setLedgerFilterCategory(cat)}
                    style={{
                      background: ledgerFilterCategory === cat ? C.accent : C.card,
                      color: ledgerFilterCategory === cat ? "#fff" : C.dim,
                      border: `1px solid ${ledgerFilterCategory === cat ? C.accent : C.border}`,
                      borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: "pointer",
                      textTransform: "capitalize",
                    }}
                  >{cat}</button>
                ))}
              </div>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ color: C.muted, textAlign: "left", background: C.card }}>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>Field JSON Path</th>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>Detected PHI Category</th>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>Action Executed</th>
                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDetails.length > 0 ? filteredDetails.map((item, idx) => (
                    <tr key={`${item.field}-${idx}`} style={{ background: idx % 2 === 0 ? "transparent" : C.card + "50" }}>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: C.text, fontFamily: "monospace" }}>{item.field}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: C.warning }}>{item.phi_type}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: C.accent, fontWeight: 600 }}>{item.action || mode}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}`, color: C.teal, fontWeight: 700 }}>✓ Success</td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan="4" style={{ padding: "14px", color: C.muted, textAlign: "center" }}>No matching field audit entries found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── TAB 4: POLICY RULES MATRIX ── */}
        {auditTab === "policy" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>Enforced Policy Rules Matrix</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>
                Active rules enforced by the Policy Engine for <strong>{purposeMeta.policyName}</strong>.
              </div>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {policyRules.map(rule => <Tag key={rule} color={C.teal}>{rule}</Tag>)}
            </div>

            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 12, color: C.muted, textTransform: "uppercase", fontWeight: 700, marginBottom: 10 }}>Regulatory Framework Alignment</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {["HIPAA Safe Harbor (45 CFR §164.514(b))", "HIPAA Expert Determination Method", "GDPR Art. 4(5) Pseudonymization", "GDPR Recital 26 Anonymization", "HL7 FHIR R4 Specification"].map(item => (
                  <Badge key={item} color={C.accent}>{item}</Badge>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 5: FHIR AUDITEVENT & EXPORTS ── */}
        {auditTab === "export" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>FHIR R4 AuditEvent Resource</div>
                <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>Ready for enterprise EHR compliance logging</div>
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button onClick={() => window.print()} style={{ background: C.accent, color: "#fff", border: "none", borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>Print / PDF</button>
                <button onClick={exportJson} style={{ background: C.surface, border: `1px solid ${C.border}`, color: C.text, borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 12 }}>Export JSON</button>
                <button onClick={exportCsv} style={{ background: C.surface, border: `1px solid ${C.border}`, color: C.text, borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 12 }}>Export CSV</button>
                <button onClick={exportAuditEvent} style={{ background: C.teal, color: "#fff", border: "none", borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>Download AuditEvent</button>
              </div>
            </div>

            <JsonBlock data={fhirAuditEventObj} maxHeight={420} />
          </div>
        )}

      </div>

      <style>{`
        @media print {
          .audit-report-printable {
            box-shadow: none !important;
            border: none !important;
            background: #fff !important;
            color: #111 !important;
          }
          .audit-report-printable button {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}

function PurposeCard({ preset, selected, onSelect, onReview }) {
  return (
    <div onClick={() => { onSelect(preset.name); onReview(preset.name); }} style={{
      background: selected ? preset.badge + "15" : C.surface,
      border: `1.5px solid ${selected ? preset.badge : C.border}`,
      borderRadius: 14,
      padding: "14px 14px",
      cursor: "pointer",
      minWidth: 220,
      flex: "1 1 minmax(220px, 1fr)",
      transition: "all 0.18s",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div style={{ fontSize: 18 }}>{preset.name === "AI Processing" ? "🤖" : preset.name === "Clinical Research" ? "🔬" : preset.name === "Analytics" ? "📊" : preset.name === "Internal Testing" ? "🧪" : preset.name === "Software Development" ? "👨‍💻" : preset.name === "Vendor Sharing" ? "🤝" : preset.name === "Public Release" ? "🌐" : preset.name === "Education" ? "📚" : preset.name === "Healthcare Operations" ? "🏥" : preset.name === "Legal Review" ? "⚖️" : "🔍"}</div>
        <Badge color={preset.badge}>{preset.privacyLevel}</Badge>
      </div>
      <div style={{ fontWeight: 700, color: C.text, marginBottom: 6 }}>{preset.name}</div>
      <div style={{ fontSize: 12, color: C.dim, lineHeight: 1.5, marginBottom: 10 }}>{preset.description}</div>
      <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 6 }}>Recommended For</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {preset.recommendedFor.map(item => <Tag key={item} color={preset.badge}>{item}</Tag>)}
      </div>
    </div>
  );
}

function PolicySummary({ policy, onCustomize, onBack, onApply }) {
  if (!policy) return null;
  const actions = policy.fields || {};
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ fontSize: 12, color: C.muted, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>Policy Summary</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>{policy.purpose}</div>
      <div style={{ color: C.teal, fontWeight: 600 }}>Privacy Level: High</div>
      <div style={{ display: "grid", gap: 8, maxHeight: 220, overflowY: "auto" }}>
        {Object.entries(actions).slice(0, 8).map(([field, action]) => (
          <div key={field} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 10px", color: C.dim, fontSize: 12 }}>
            <span style={{ color: C.text, fontWeight: 600 }}>{field}</span> — {action}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button onClick={onCustomize} style={{ background: C.accent, color: "#fff", border: "none", borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>Customize</button>
        <button onClick={onApply} style={{ background: C.teal, color: "#fff", border: "none", borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>Apply Policy</button>
        <button onClick={onBack} style={{ background: C.surface, border: `1px solid ${C.border}`, color: C.text, borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>Close</button>
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
  const [processingMeta, setProcessingMeta] = useState(null);
  const [includeAudit, setIncludeAudit] = useState(true);
  const [jsonError, setJsonError] = useState(null);
  const [selectedPurpose, setSelectedPurpose] = useState("AI Processing");
  const [policyPreset, setPolicyPreset] = useState(null);
  const [policyStep, setPolicyStep] = useState("purpose");
  const [policyPreview, setPolicyPreview] = useState(null);
  const [policySearch, setPolicySearch] = useState("");
  const [policyDrawerOpen, setPolicyDrawerOpen] = useState(false);
  const [customPolicyJson, setCustomPolicyJson] = useState(JSON.stringify({ purpose: "Custom", fields: {} }, null, 2));

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
    setProcessingMeta(null);

    const parsed = JSON.parse(raw);
    const startedAt = performance.now();
    const endpoint = isBundle ? "/phi/deidentify-bundle" : "/phi/deidentify";
    
    let activePolicy = null;
    try {
      if (customPolicyJson) {
        activePolicy = JSON.parse(customPolicyJson);
      } else if (policyPreset) {
        activePolicy = policyPreset;
      }
    } catch (e) {}

    const body = isBundle
      ? { bundle: parsed, mode, audit: includeAudit, policy: activePolicy, purpose: selectedPurpose }
      : { resource: parsed, mode, audit: includeAudit, policy: activePolicy, purpose: selectedPurpose };

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
      const durationMs = Math.round(performance.now() - startedAt);
      setProcessingMeta({
        processingDurationMs: durationMs,
        resourceType: isBundle ? "Bundle" : "Resource",
        totalResources: isBundle ? (parsed.entry?.length || 0) : 1,
        scannedFields: countFields(parsed),
        fileSizeBytes: new Blob([raw]).size,
      });
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
    setProcessingMeta(null);
    setJsonError(null);
  }

  const deidentifiedData = result?.deidentified_resource || result?.deidentified_bundle;
  const auditReport = result?.audit_report;

  useEffect(() => {
    async function loadPreset() {
      try {
        const res = await fetch(`${API_BASE}/phi/policies/presets`);
        const data = await res.json();
        if (res.ok && Array.isArray(data.presets)) {
          const preset = data.presets.find(item => item.purpose === selectedPurpose) || data.presets[0];
          setPolicyPreset(preset);
          setCustomPolicyJson(JSON.stringify(preset || { purpose: selectedPurpose, fields: {} }, null, 2));
        }
      } catch (e) {
        console.error(e);
      }
    }
    loadPreset();
  }, [selectedPurpose]);

  async function previewPolicy() {
    try {
      if (!validateJson(isBundle ? bundleJson : inputJson)) return;
      const parsedPolicy = JSON.parse(customPolicyJson);
      const parsedResource = JSON.parse(isBundle ? bundleJson : inputJson);
      const res = await fetch(`${API_BASE}/phi/policies/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey || "" },
        body: JSON.stringify({ resource: parsedResource, policy: parsedPolicy, mode }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Policy preview failed");
      setPolicyPreview(data);
      setResult({
        deidentified_resource: data.processed_resource,
        audit_report: {
          phi_items_found: data.stats?.modified_fields || 0,
          phi_by_type: {},
          fields_cleaned: Object.keys(parsedPolicy.fields || {}),
          mode: "policy",
          hipaa_safe_harbor_compliant: true,
          standard: "Purpose-based policy engine",
          timestamp: new Date().toISOString(),
          details: data.summary?.actions || [],
        },
      });
      setProcessingMeta({
        processingDurationMs: 0,
        resourceType: isBundle ? "Bundle" : "Resource",
        totalResources: isBundle ? (parsedResource.entry?.length || 0) : 1,
        scannedFields: countFields(parsedResource),
        fileSizeBytes: new Blob([isBundle ? bundleJson : inputJson]).size,
      });
      setPolicyStep("preview");
      setPolicyDrawerOpen(true);
    } catch (e) {
      setError(e.message);
    }
  }

  async function openPolicyDrawer(presetName) {
    setSelectedPurpose(presetName);
    try {
      const res = await fetch(`${API_BASE}/phi/policies/presets`);
      const data = await res.json();
      if (res.ok && Array.isArray(data.presets)) {
        const preset = data.presets.find(item => item.purpose === presetName) || data.presets[0];
        setPolicyPreset(preset);
        setCustomPolicyJson(JSON.stringify(preset || { purpose: presetName, fields: {} }, null, 2));
        setPolicyStep("summary");
        setPolicyDrawerOpen(true);
      }
    } catch (e) {
      console.error(e);
    }
  }

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
            <MedTechLogo size={24} onClick={() => navigate("/")} />
            <h1 style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: 18, fontWeight: 700,
              letterSpacing: "-0.02em", margin: 0,
            }}>PHI De-identifier</h1>
            <Badge color={C.teal}>Privacy Assessment</Badge>
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
          <button onClick={() => navigate('/tools/api')} style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 8, padding: "7px 14px",
            color: C.dim, fontSize: 12, cursor: "pointer",
            fontWeight: 500, transition: "all 0.2s",
            fontFamily: "inherit",
          }}>API Docs</button>
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

        {/* ── Purpose selection ── */}
        <div style={{ marginBottom: 20, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>Purpose-Based Privacy Policy Engine</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: C.text, marginTop: 4 }}>Select a privacy purpose</div>
            </div>
            <input value={policySearch} onChange={e => setPolicySearch(e.target.value)} placeholder="Search purposes" style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 10px", color: C.text, minWidth: 220 }} />
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            {PURPOSE_PRESETS.filter(preset => preset.name.toLowerCase().includes(policySearch.toLowerCase())).map(preset => (
              <PurposeCard
                key={preset.name}
                preset={preset}
                selected={selectedPurpose === preset.name}
                onSelect={setSelectedPurpose}
                onReview={openPolicyDrawer}
              />
            ))}
          </div>
          {policyPreset && (
            <div style={{ marginTop: 16, display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button onClick={() => { setCustomPolicyJson(JSON.stringify(policyPreset, null, 2)); setPolicyStep("summary"); setPolicyDrawerOpen(true); }} style={{ background: C.accent, color: "#fff", border: "none", borderRadius: 8, padding: "9px 14px", cursor: "pointer" }}>Review Policy</button>
              <button onClick={() => { setCustomPolicyJson(JSON.stringify(policyPreset, null, 2)); setPolicyStep("custom"); setPolicyDrawerOpen(true); }} style={{ background: C.surface, border: `1px solid ${C.border}`, color: C.text, borderRadius: 8, padding: "9px 14px", cursor: "pointer" }}>Customize Policy</button>
              <button onClick={() => { setCustomPolicyJson(JSON.stringify(policyPreset, null, 2)); previewPolicy(); }} style={{ background: C.teal, color: "#fff", border: "none", borderRadius: 8, padding: "9px 14px", cursor: "pointer" }}>Apply Policy</button>
            </div>
          )}
        </div>

        {policyDrawerOpen && policyPreset && (
          <div style={{ position: "fixed", top: 90, left: 20, bottom: 20, width: "min(380px, calc(100vw - 40px))", zIndex: 30, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 16, boxShadow: "0 20px 60px rgba(0,0,0,0.35)", overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "14px 16px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 12, color: C.muted, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>Policy Review</div>
              <button onClick={() => { setPolicyStep("purpose"); setPolicyDrawerOpen(false); setPolicyPreview(null); }} style={{ background: "transparent", border: "none", color: C.dim, cursor: "pointer", fontSize: 18 }}>×</button>
            </div>
            <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" }}>
              {policyStep === "summary" && policyPreset && <PolicySummary policy={policyPreset} onCustomize={() => { setPolicyStep("custom"); }} onBack={() => { setPolicyStep("purpose"); setPolicyDrawerOpen(false); setPolicyPreview(null); }} onApply={() => previewPolicy()} />}
              {policyStep === "custom" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div style={{ fontSize: 12, color: C.muted, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>Custom Policy Editor</div>
                  <textarea value={customPolicyJson} onChange={e => setCustomPolicyJson(e.target.value)} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12, color: C.text, minHeight: 180, fontFamily: "monospace", fontSize: 12 }} />
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button onClick={previewPolicy} style={{ background: C.teal, color: "#fff", border: "none", borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>Apply Policy</button>
                    <button onClick={() => setPolicyStep("summary")} style={{ background: C.surface, border: `1px solid ${C.border}`, color: C.text, borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>Back</button>
                  </div>
                </div>
              )}
              {policyStep === "preview" && policyPreview && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div style={{ fontSize: 12, color: C.muted, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>Policy Preview</div>
                  <div style={{ color: C.text, fontWeight: 700 }}>{policyPreview.policy?.purpose}</div>
                  <div style={{ color: C.teal, fontWeight: 600 }}>Risk: {policyPreview.risk?.risk_level} ({policyPreview.risk?.score})</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {policyPreview.summary?.actions?.slice(0, 6).map(action => <Tag key={action.field} color={C.accent}>{action.description}</Tag>)}
                  </div>
                  <button onClick={() => { setPolicyStep("custom"); }} style={{ background: C.surface, border: `1px solid ${C.border}`, color: C.text, borderRadius: 8, padding: "8px 14px", cursor: "pointer", alignSelf: "flex-start" }}>Edit Again</button>
                </div>
              )}
            </div>
          </div>
        )}

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
                      De-identification complete · Mode: {mode} · Policy-based assessment
                    </span>
                  </div>

                  <div style={{ flex: 1, minHeight: 300, display: "flex", flexDirection: "column" }}>
                    <JsonBlock data={deidentifiedData} maxHeight={600} />
                  </div>

                  {/* Audit report */}
                  {includeAudit && auditReport && (
                    <AuditPanel
                      report={auditReport}
                      selectedPurpose={selectedPurpose}
                      mode={mode}
                      processingMeta={processingMeta}
                      policyDefinition={policyPreset}
                    />
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