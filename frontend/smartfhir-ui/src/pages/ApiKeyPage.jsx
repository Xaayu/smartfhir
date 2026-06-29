import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0A0E1A;
    color: #E2E8F0;
    font-family: 'Inter', system-ui, sans-serif;
  }

  .key-page {
    min-height: 100vh;
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
    gap: 56px;
    padding: 56px;
    background:
      radial-gradient(circle at top left, rgba(79,142,247,0.18), transparent 32%),
      radial-gradient(circle at bottom right, rgba(0,212,170,0.12), transparent 28%),
      #0A0E1A;
  }

  .key-brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #E2E8F0;
    text-decoration: none;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 18px;
    margin-bottom: 72px;
  }

  .key-logo {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, #4F8EF7, #00D4AA);
    display: grid;
    place-items: center;
    color: #fff;
    font-weight: 800;
  }

  .key-eyebrow {
    color: #4F8EF7;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 14px;
  }

  .key-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(38px, 5vw, 64px);
    line-height: 1.02;
    letter-spacing: -0.03em;
    max-width: 720px;
    margin-bottom: 22px;
  }

  .key-copy {
    color: #94A3B8;
    font-size: 18px;
    line-height: 1.7;
    max-width: 580px;
    margin-bottom: 40px;
  }

  .benefit-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    max-width: 720px;
  }

  .benefit {
    border: 1px solid #242B42;
    background: rgba(26, 32, 53, 0.72);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }

  .benefit-mark {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    display: grid;
    place-items: center;
    background: rgba(0,212,170,0.12);
    color: #00D4AA;
    border: 1px solid rgba(0,212,170,0.28);
    font-size: 13px;
    font-weight: 800;
    flex: 0 0 auto;
  }

  .benefit-title {
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 3px;
  }

  .benefit-desc {
    color: #64748B;
    font-size: 13px;
    line-height: 1.5;
  }

  .key-form-wrap {
    align-self: center;
    border: 1px solid #242B42;
    background: rgba(26, 32, 53, 0.86);
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 28px 70px rgba(0,0,0,0.32);
  }

  .key-form-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .key-form-sub {
    color: #94A3B8;
    font-size: 14px;
    margin-bottom: 24px;
  }

  .key-label {
    display: block;
    color: #94A3B8;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .key-input {
    width: 100%;
    background: #0A0E1A;
    border: 1px solid #242B42;
    color: #E2E8F0;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 15px;
    outline: none;
    margin-bottom: 14px;
  }

  .key-input:focus {
    border-color: #4F8EF7;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.15);
  }

  .key-button {
    width: 100%;
    background: #4F8EF7;
    border: 0;
    color: #fff;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 15px;
    font-weight: 800;
    cursor: pointer;
    transition: transform 0.18s, background 0.18s, opacity 0.18s;
  }

  .key-button:hover { background: #6B9EF8; transform: translateY(-1px); }
  .key-button:disabled { cursor: wait; opacity: 0.7; transform: none; }

  .key-error {
    color: #F87171;
    font-size: 13px;
    margin-top: 12px;
  }

  .key-message {
    margin-top: 18px;
    padding: 16px 18px;
    border-radius: 18px;
    background: rgba(16, 185, 129, 0.12);
    color: #A7F3D0;
    font-size: 14px;
    line-height: 1.6;
  }

  .key-snippet {
    margin-top: 24px;
    border: 1px solid #242B42;
    border-radius: 10px;
    background: #060A14;
    padding: 14px;
    font-family: 'JetBrains Mono', monospace;
    color: #64748B;
    font-size: 12px;
    line-height: 1.7;
  }

  .key-snippet span { color: #00D4AA; }

  .key-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 24px 0;
    color: #64748B;
    font-size: 13px;
  }

  .key-divider::before,
  .key-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #242B42;
  }

  @media (max-width: 900px) {
    .key-page {
      grid-template-columns: 1fr;
      padding: 28px 20px 40px;
      gap: 36px;
    }

    .key-brand { margin-bottom: 40px; }
    .benefit-grid { grid-template-columns: 1fr; }
    .key-form-wrap { align-self: stretch; }
  }
`;

const benefits = [
  ["Instant API Key", "Start testing the API as soon as you submit your email."],
  ["500 Free API Calls", "Enough room to validate real workflows before paying."],
  ["FHIR Validation", "Catch resource errors with developer-friendly responses."],
  ["Auto Fix", "Normalize common date, gender, status, and enum mistakes."],
  ["Mapping", "Convert messy field names into clean FHIR fields."],
  ["Bundle Generation", "Coming soon for multi-resource workflows."],
  ["No Credit Card Required", "V1 is built for fast product validation."],
];

export default function ApiKeyPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function registerEmail(e) {
    e.preventDefault();
    const trimmedEmail = email.trim();

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setError("Enter a valid email address.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const res = await fetch(`${API_BASE}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmedEmail }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Could not create API key.");
        setLoading(false);
        return;
      }

      // Persist and redirect to dashboard
      localStorage.setItem("smartfhirEmail", data.email);
      localStorage.setItem("smartfhirApiKey", data.api_key);
      localStorage.setItem("smartfhirPlan", data.plan || "Free");
      localStorage.setItem("smartfhirUsage", String(data.calls_used || 0));
      localStorage.setItem("smartfhirLimit", String(data.calls_limit || 500));
      navigate("/dashboard");
    } catch (e) {
      setError(`Cannot connect to the MedTechTools API at ${API_BASE}.`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <style>{styles}</style>
      <main className="key-page">
        <section>
          <button className="key-brand" onClick={() => navigate("/")} style={{ background: "none", border: 0, cursor: "pointer" }}>
            <span className="key-logo">M</span>
            MedTechTools
          </button>

          <div className="key-eyebrow">Developer preview</div>
          <h1 className="key-title">Get a MedTechTools API key in one step.</h1>
          <p className="key-copy">
            V1 is intentionally small: one email, one key, and a dashboard for testing validation,
            mapping, and auto-fix workflows.
          </p>

          <div className="benefit-grid">
            {benefits.map(([title, desc]) => (
              <div className="benefit" key={title}>
                <div className="benefit-mark">{title === "Bundle Generation" ? ">" : "+"}</div>
                <div>
                  <div className="benefit-title">{title}</div>
                  <div className="benefit-desc">{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="key-form-wrap">
          <h2 className="key-form-title">Create your free key</h2>
          <p className="key-form-sub">No password. No trial setup. No credit card.</p>

          <form onSubmit={registerEmail}>
            <label className="key-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              className="key-input"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={e => {
                setEmail(e.target.value);
                setError("");
                setMessage("");
              }}
              autoComplete="email"
            />
            <button className="key-button" disabled={loading}>
              {loading ? "Creating API key..." : "Create my API key"}
            </button>
          </form>

          {message && <div className="key-message">{message}</div>}
          {error && <div className="key-error">{error}</div>}

          {/* OAuth removed — email-only flow */}

          <div className="key-snippet">
            curl -H <span>"X-API-Key: sk_live_..."</span> https://api.medtechtools.io/validate
          </div>
        </section>
      </main>
    </>
  );
}
