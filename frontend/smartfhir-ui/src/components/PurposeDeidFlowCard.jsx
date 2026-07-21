import React, { useState } from "react";

const PURPOSES = [
  {
    id: "clinical_research",
    name: "Clinical Research",
    icon: "🔬",
    privacyLevel: "High Privacy",
    description: "Optimized for cohort studies and academic research while preserving clinical data utility.",
    rules: [
      { field: "patient_name", action: "REMOVE", detail: "Direct identifier removed" },
      { field: "phone / email", action: "REMOVE", detail: "Contact info purged" },
      { field: "address", action: "CITY_ONLY", detail: "Generalize to City & State" },
      { field: "date_of_birth", action: "YEAR_ONLY", detail: "Keep birth year for age cohorting" },
      { field: "encounter_dates", action: "SHIFT_DATE", detail: "Shift dates deterministically (+/- 14d)" },
      { field: "patient_id", action: "HASH", detail: "SHA-256 HMAC pseudonym" },
      { field: "clinical_notes", action: "KEEP", detail: "Preserved for medical NLP" },
    ]
  },
  {
    id: "ai_processing",
    name: "AI & Model Training",
    icon: "🤖",
    privacyLevel: "Strict Privacy",
    description: "Tailored for LLM and ML model training to prevent memorization of identifiable patient entities.",
    rules: [
      { field: "patient_name", action: "PSEUDONYMIZE", detail: "Replaced with realistic synthetic name" },
      { field: "phone / email", action: "MASK", detail: "J*** D** format" },
      { field: "address", action: "STATE_ONLY", detail: "Truncate to State" },
      { field: "date_of_birth", action: "AGE_GROUP", detail: "Group into 5-year age brackets" },
      { field: "encounter_dates", action: "YEAR_ONLY", detail: "Retain observation year" },
      { field: "patient_id", action: "SYNTHETIC", detail: "Generated UUID" },
      { field: "clinical_notes", action: "SCAN_REDACT", detail: "Free-text PHI scanner redacts names/phones" },
    ]
  },
  {
    id: "vendor_sharing",
    name: "Vendor Sharing",
    icon: "🤝",
    privacyLevel: "HIPAA Safe Harbor",
    description: "Safe multi-tenant sharing with 3rd-party SaaS vendors and test environment deployments.",
    rules: [
      { field: "patient_name", action: "PSEUDONYMIZE", detail: "HIPAA Safe Harbor fake name generator" },
      { field: "phone / email", action: "REMOVE", detail: "Purged from record" },
      { field: "address", action: "3_DIGIT_ZIP", detail: "3-digit ZIP prefix rule" },
      { field: "date_of_birth", action: "YEAR_ONLY", detail: "Year only (if age < 89)" },
      { field: "encounter_dates", action: "SHIFT_DATE", detail: "Randomized uniform offset per patient" },
      { field: "patient_id", action: "HASH", detail: "Consistent key mapping" },
      { field: "clinical_notes", action: "MASK", detail: "PHI tokens masked with asterisks" },
    ]
  },
  {
    id: "public_release",
    name: "Public Release",
    icon: "🌐",
    privacyLevel: "Maximum Privacy",
    description: "Maximum de-identification for open science datasets and public health disclosures.",
    rules: [
      { field: "patient_name", action: "REDACTED", detail: "Replaced with [REDACTED]" },
      { field: "phone / email", action: "REDACTED", detail: "Replaced with [REDACTED]" },
      { field: "address", action: "REMOVE", detail: "All location data purged" },
      { field: "date_of_birth", action: "AGE_DECADE", detail: "Decade bracket (e.g. 30-39)" },
      { field: "encounter_dates", action: "REMOVE", detail: "All timestamps suppressed" },
      { field: "patient_id", action: "ANONYMOUS", detail: "Sequential ID (PAT-0001)" },
      { field: "clinical_notes", action: "REMOVE", detail: "Unstructured text removed" },
    ]
  }
];

const ACTION_COLORS = {
  REMOVE: { bg: "#F8717122", color: "#F87171", border: "#F8717144" },
  REDACTED: { bg: "#EF444422", color: "#EF4444", border: "#EF444444" },
  PSEUDONYMIZE: { bg: "#10B98122", color: "#10B981", border: "#10B98144" },
  MASK: { bg: "#F59E0B22", color: "#F59E0B", border: "#F59E0B44" },
  CITY_ONLY: { bg: "#3B82F622", color: "#3B82F6", border: "#3B82F644" },
  STATE_ONLY: { bg: "#3B82F622", color: "#3B82F6", border: "#3B82F644" },
  "3_DIGIT_ZIP": { bg: "#3B82F622", color: "#3B82F6", border: "#3B82F644" },
  YEAR_ONLY: { bg: "#8B5CF622", color: "#8B5CF6", border: "#8B5CF644" },
  AGE_GROUP: { bg: "#8B5CF622", color: "#8B5CF6", border: "#8B5CF644" },
  AGE_DECADE: { bg: "#8B5CF622", color: "#8B5CF6", border: "#8B5CF644" },
  SHIFT_DATE: { bg: "#EC489922", color: "#EC4899", border: "#EC489944" },
  HASH: { bg: "#6366F122", color: "#6366F1", border: "#6366F144" },
  SYNTHETIC: { bg: "#6366F122", color: "#6366F1", border: "#6366F144" },
  ANONYMOUS: { bg: "#6366F122", color: "#6366F1", border: "#6366F144" },
  KEEP: { bg: "#10B98122", color: "#10B981", border: "#10B98144" },
  SCAN_REDACT: { bg: "#F59E0B22", color: "#F59E0B", border: "#F59E0B44" },
};

export default function PurposeDeidFlowCard({ colors }) {
  const [selectedPurposeId, setSelectedPurposeId] = useState("clinical_research");

  const currentPurpose = PURPOSES.find(p => p.id === selectedPurposeId) || PURPOSES[0];

  return (
    <div style={{
      background: colors.surface,
      border: `1px solid ${colors.border}`,
      borderRadius: 16,
      padding: 24,
      marginBottom: 32,
      boxShadow: `0 4px 20px ${colors.shadow}`,
    }}>
      {/* Visual Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          padding: "4px 10px",
          borderRadius: 20,
          background: "rgba(16, 185, 129, 0.15)",
          color: "#10B981",
          fontSize: 12,
          fontWeight: 700,
          marginBottom: 10,
          textTransform: "uppercase",
          letterSpacing: "0.05em"
        }}>
          <span>🛡️ Purpose-Based Architecture & Flow</span>
        </div>
        <h3 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 6px" }}>
          Purpose-Driven De-Identification Data Flow
        </h3>
        <p style={{ color: colors.textDim, fontSize: 14, margin: 0, maxWidth: 800 }}>
          Instead of blanket redaction, MedTechTools evaluates data usage intent and applies HIPAA-aligned policy rules per purpose.
        </p>
      </div>

      {/* Workflow Step Pipeline Nodes */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: 12,
        marginBottom: 28,
        position: "relative"
      }}>
        {/* Node 1 */}
        <div style={{
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 16,
          display: "flex",
          flexDirection: "column",
          gap: 8
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 22 }}>📥</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: colors.accent, background: colors.accent + "18", padding: "2px 8px", borderRadius: 10 }}>
              STEP 1
            </span>
          </div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>Raw PHI Input</div>
          <div style={{ fontSize: 12, color: colors.textDim, lineHeight: 1.5 }}>
            FHIR Resource, Bundle, or Unstructured Clinical Text containing sensitive identifiers.
          </div>
        </div>

        {/* Node 2 */}
        <div style={{
          background: colors.bg,
          border: `1px solid #10B98144`,
          borderRadius: 12,
          padding: 16,
          display: "flex",
          flexDirection: "column",
          gap: 8
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 22 }}>🎯</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: "#10B981", background: "#10B98118", padding: "2px 8px", borderRadius: 10 }}>
              STEP 2
            </span>
          </div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>Specify Purpose</div>
          <div style={{ fontSize: 12, color: colors.textDim, lineHeight: 1.5 }}>
            Define usage scope (Research, AI, Vendor, Public) in request body: <code>"purpose": "..."</code>
          </div>
        </div>

        {/* Node 3 */}
        <div style={{
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 16,
          display: "flex",
          flexDirection: "column",
          gap: 8
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 22 }}>⚙️</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: colors.accent, background: colors.accent + "18", padding: "2px 8px", borderRadius: 10 }}>
              STEP 3
            </span>
          </div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>Policy Executor</div>
          <div style={{ fontSize: 12, color: colors.textDim, lineHeight: 1.5 }}>
            Applies targeted field transforms: Redact, Mask, Hash, Pseudonymize, or Shift Dates.
          </div>
        </div>

        {/* Node 4 */}
        <div style={{
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 16,
          display: "flex",
          flexDirection: "column",
          gap: 8
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 22 }}>🛡️</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: "#34D399", background: "#34D39918", padding: "2px 8px", borderRadius: 10 }}>
              STEP 4
            </span>
          </div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>De-Identified Output</div>
          <div style={{ fontSize: 12, color: colors.textDim, lineHeight: 1.5 }}>
            Returns compliant payload + <code>audit_report</code> detailing applied transformations.
          </div>
        </div>
      </div>

      {/* Purpose Rule Selector & Interactive Matrix */}
      <div style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: 14,
        padding: 20
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>Interactive Purpose Rules Matrix</div>
            <div style={{ color: colors.textDim, fontSize: 13, marginTop: 2 }}>
              Select a purpose below to preview its field transformation policy
            </div>
          </div>
          <div style={{
            fontSize: 12,
            fontWeight: 600,
            padding: "4px 10px",
            borderRadius: 20,
            background: "#10B98120",
            color: "#10B981",
            border: "1px solid #10B98140"
          }}>
            {currentPurpose.privacyLevel}
          </div>
        </div>

        {/* Purpose Buttons */}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 20 }}>
          {PURPOSES.map((p) => {
            const isSelected = p.id === selectedPurposeId;
            return (
              <button
                key={p.id}
                onClick={() => setSelectedPurposeId(p.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "10px 14px",
                  borderRadius: 10,
                  border: `1px solid ${isSelected ? "#10B981" : colors.border}`,
                  background: isSelected ? "#10B98118" : colors.surface,
                  color: isSelected ? "#10B981" : colors.text,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s ease"
                }}
              >
                <span>{p.icon}</span>
                <span>{p.name}</span>
              </button>
            );
          })}
        </div>

        {/* Description */}
        <div style={{
          fontSize: 13,
          color: colors.textDim,
          marginBottom: 16,
          padding: "10px 14px",
          borderRadius: 8,
          background: colors.surface,
          borderLeft: "3px solid #10B981"
        }}>
          {currentPurpose.description}
        </div>

        {/* Rules Table */}
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${colors.border}`, textAlign: "left" }}>
                <th style={{ padding: "10px 12px", color: colors.textDim, fontWeight: 600 }}>Field Category</th>
                <th style={{ padding: "10px 12px", color: colors.textDim, fontWeight: 600 }}>Applied Action</th>
                <th style={{ padding: "10px 12px", color: colors.textDim, fontWeight: 600 }}>Policy Details</th>
              </tr>
            </thead>
            <tbody>
              {currentPurpose.rules.map((rule, idx) => {
                const style = ACTION_COLORS[rule.action] || { bg: "#64748B22", color: "#64748B", border: "#64748B44" };
                return (
                  <tr key={idx} style={{ borderBottom: `1px solid ${colors.border}55` }}>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace", color: colors.text, fontWeight: 600 }}>
                      {rule.field}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <span style={{
                        display: "inline-block",
                        padding: "3px 8px",
                        borderRadius: 6,
                        fontSize: 11,
                        fontWeight: 700,
                        background: style.bg,
                        color: style.color,
                        border: `1px solid ${style.border}`
                      }}>
                        {rule.action}
                      </span>
                    </td>
                    <td style={{ padding: "10px 12px", color: colors.textDim }}>
                      {rule.detail}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
