import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TryWithApiCard from "../components/TryWithApiCard";
import { API_BASE } from "../config";
import { API_SUITES, buildEndpointUrl } from "../data/apiSuitesData";

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
  },
};

function getApiHeaders() {
  const apiKey = localStorage.getItem("smartfhirApiKey");
  return {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  };
}


export default function ApiPage() {
  const navigate = useNavigate();
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("smartfhirTheme");
    return saved || "dark";
  });
  const [selectedSuite, setSelectedSuite] = useState("fhir");
  const [selectedResource, setSelectedResource] = useState(() => API_SUITES.fhir.resources[0]);
  const colors = THEMES[theme];

  const currentSuite = API_SUITES[selectedSuite];
  const currentResource = selectedResource || currentSuite.resources[0];
  const currentEndpoint = buildEndpointUrl(
    `${API_BASE}${currentResource.endpoint}`,
    currentResource.queryParams
  );
  const currentHeaders = getApiHeaders();

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("smartfhirTheme", newTheme);
  };


  return (
    <div style={{ minHeight: "100vh", background: colors.bg, color: colors.text, fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Header */}
      <header style={{
        position: "sticky",
        top: 0,
        zIndex: 100,
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        padding: "14px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        boxShadow: `0 2px 8px ${colors.shadow}`,
      }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 17 }}>API Documentation</div>
          <div style={{ color: colors.textDim, fontSize: 12, marginTop: 2 }}>
            Multi-suite API playground for FHIR, HL7, and Terminology
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button
            onClick={toggleTheme}
            style={{
              width: 34,
              height: 34,
              borderRadius: 10,
              border: `1px solid ${colors.border}`,
              display: "grid",
              placeItems: "center",
              background: "transparent",
              color: colors.text,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            {theme === "dark" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
          <button
            onClick={() => navigate("/tools")}
            style={{
              border: `1px solid ${colors.border}`,
              background: "transparent",
              color: colors.text,
              borderRadius: 10,
              padding: "8px 12px",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(128,128,128,0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            ← Back to Tools
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 16px 64px" }}>
        {/* Step 1: Suite Selection */}
        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Step 1: Select Your Suite</h2>
          <p style={{ color: colors.textDim, fontSize: 14, marginBottom: 20 }}>
            Choose the product suite you want to work with
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 16 }}>
            {Object.values(API_SUITES).map((suite) => (
              <button
                key={suite.id}
                onClick={() => {
                  setSelectedSuite(suite.id);
                  setSelectedResource(suite.resources[0]);
                }}
                style={{
                  padding: "20px",
                  borderRadius: 12,
                  border: `2px solid ${selectedSuite === suite.id ? suite.color : colors.border}`,
                  background: selectedSuite === suite.id ? suite.color + "15" : colors.surface,
                  color: colors.text,
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.3s ease",
                  textAlign: "left",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}
                onMouseEnter={(e) => {
                  if (selectedSuite !== suite.id) {
                    e.currentTarget.style.borderColor = suite.color;
                    e.currentTarget.style.transform = "translateY(-2px)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedSuite !== suite.id) {
                    e.currentTarget.style.borderColor = colors.border;
                    e.currentTarget.style.transform = "translateY(0)";
                  }
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontSize: 28 }}>{suite.icon}</span>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>{suite.name}</div>
                </div>
                <div style={{ color: colors.textDim, fontSize: 13, fontWeight: 400 }}>
                  {suite.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Resource/Action Selection */}
        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Step 2: Select Resource / Action</h2>
          <p style={{ color: colors.textDim, fontSize: 14, marginBottom: 20 }}>
            Choose the specific API endpoint for {currentSuite.name}
          </p>
          <div style={{
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: 10,
            padding: 8,
            overflowX: "auto",
          }}>
            {currentSuite.resources.map((resource) => (
              <button
                key={resource.id}
                onClick={() => setSelectedResource(resource)}
                style={{
                  padding: "10px 14px",
                  borderRadius: 8,
                  border: "none",
                  background: selectedResource?.id === resource.id ? currentSuite.color + "20" : "transparent",
                  color: selectedResource?.id === resource.id ? currentSuite.color : colors.text,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  whiteSpace: "nowrap",
                }}
                onMouseEnter={(e) => {
                  if (selectedResource?.id !== resource.id) {
                    e.currentTarget.style.background = colors.border;
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedResource?.id !== resource.id) {
                    e.currentTarget.style.background = "transparent";
                  }
                }}
              >
                {resource.name}
              </button>
            ))}
          </div>
        </div>

        {/* Resource Details */}
        <div style={{
          background: colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 20,
          marginBottom: 32,
        }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{currentResource.name}</h3>
          <p style={{ color: colors.textDim, fontSize: 14, marginBottom: 16 }}>{currentResource.description}</p>
          
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 16 }}>
            <div>
              <div style={{ color: colors.textDim, fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Method</div>
              <div style={{
                display: "inline-block",
                padding: "4px 8px",
                borderRadius: 4,
                background: currentResource.method === "GET" ? colors.success + "22" : colors.accent + "22",
                color: currentResource.method === "GET" ? colors.success : colors.accent,
                fontSize: 13,
                fontWeight: 700,
              }}>
                {currentResource.method}
              </div>
            </div>
            <div>
              <div style={{ color: colors.textDim, fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Endpoint</div>
              <div style={{ fontSize: 13, fontFamily: "monospace", color: colors.text }}>
                {currentResource.endpoint}
              </div>
            </div>
          </div>
        </div>

        {/* Step 3: Interactive Code Snippet Card */}
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Step 3: Try with API</h2>
          <p style={{ color: colors.textDim, fontSize: 14, marginBottom: 20 }}>
            Copy and run this code to interact with the {currentSuite.name} API
          </p>
          <TryWithApiCard
            endpoint={currentEndpoint}
            method={currentResource.method}
            headers={currentHeaders}
            body={currentResource.body}
            colors={colors}
          />
        </div>
      </main>
    </div>
  );
}