import { useState } from "react";
import { useNavigate } from "react-router-dom";

const COLORS = {
  bg: "#0F1117",
  surface: "#1A1D27",
  border: "#2A2D3E",
  accent: "#4F8EF7",
  success: "#34D399",
  error: "#F87171",
  muted: "#6B7280",
  text: "#E2E8F0",
  textDim: "#94A3B8",
};

export default function AdminGate() {
  const navigate = useNavigate();
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    if (!token.trim()) {
      setError("Please enter admin token");
      return;
    }

    setLoading(true);
    setError("");

    // Store token in localStorage
    localStorage.setItem("smartfhirAdminToken", token.trim());
    
    // Navigate to admin panel
    navigate("/admin");
  }

  return (
    <main style={{
      minHeight: "100vh",
      background: COLORS.bg,
      color: COLORS.text,
      fontFamily: "'Inter', system-ui, sans-serif",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
    }}>
      <div style={{
        background: COLORS.surface,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 12,
        padding: 40,
        maxWidth: 400,
        width: "100%",
        boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
      }}>
        <h1 style={{ fontSize: 24, margin: "0 0 12px", fontWeight: 700 }}>Admin Access</h1>
        <p style={{ color: COLORS.textDim, fontSize: 14, marginBottom: 24, lineHeight: 1.5 }}>
          Enter your admin token to access the founder analytics dashboard.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 20 }}>
            <label style={{ 
              display: "block", 
              color: COLORS.textDim, 
              fontSize: 12, 
              fontWeight: 600, 
              marginBottom: 8,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
            }}>
              Admin Token
            </label>
            <input
              type="password"
              value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="Enter admin token"
              style={{
                width: "100%",
                background: COLORS.bg,
                border: `1px solid ${COLORS.border}`,
                borderRadius: 8,
                padding: "12px 14px",
                color: COLORS.text,
                fontSize: 14,
                outline: "none",
                transition: "border-color 0.2s",
              }}
              onFocus={e => e.target.style.borderColor = COLORS.accent}
              onBlur={e => e.target.style.borderColor = COLORS.border}
            />
          </div>

          {error && (
            <div style={{
              background: "rgba(248,113,113,0.1)",
              border: `1px solid ${COLORS.error}44`,
              borderRadius: 8,
              padding: "10px 12px",
              color: COLORS.error,
              fontSize: 13,
              marginBottom: 16,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              background: COLORS.accent,
              border: 0,
              color: "#fff",
              borderRadius: 8,
              padding: "12px",
              fontSize: 14,
              fontWeight: 700,
              cursor: loading ? "wait" : "pointer",
              transition: "all 0.2s",
            }}
            onMouseOver={e => !loading && (e.target.style.background = "#6B9EF8")}
            onMouseOut={e => !loading && (e.target.style.background = COLORS.accent)}
          >
            {loading ? "Accessing..." : "Access Admin Panel"}
          </button>
        </form>

        <button
          onClick={() => navigate("/")}
          style={{
            width: "100%",
            background: "transparent",
            border: 0,
            color: COLORS.muted,
            padding: "12px",
            fontSize: 13,
            cursor: "pointer",
            marginTop: 12,
            transition: "color 0.2s",
          }}
          onMouseOver={e => e.target.style.color = COLORS.text}
          onMouseOut={e => e.target.style.color = COLORS.muted}
        >
          ← Back to home
        </button>
      </div>
    </main>
  );
}
