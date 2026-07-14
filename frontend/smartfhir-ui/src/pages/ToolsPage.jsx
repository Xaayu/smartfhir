import { useNavigate } from "react-router-dom";

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

  * { box-sizing: border-box; }
  body { margin: 0; }

  :root {
    --bg: #0A0E1A;
    --surface: #1A2035;
    --border: #242B42;
    --accent: #4F8EF7;
    --teal: #00D4AA;
    --text: #E2E8F0;
    --muted: #64748B;
    --dim: #94A3B8;
  }

  .tools-page {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
  }

  .tools-shell {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }

  .tools-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 28px;
  }

  .tools-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 18px;
    cursor: pointer;
  }

  .tools-brand-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--accent), var(--teal));
    color: #fff;
    font-weight: 800;
  }

  .tools-hero {
    background: linear-gradient(135deg, rgba(79,142,247,0.14), rgba(0,212,170,0.08));
    border: 1px solid rgba(79,142,247,0.2);
    border-radius: 24px;
    padding: 36px;
    margin-bottom: 24px;
  }

  .tools-eyebrow {
    display: inline-block;
    margin-bottom: 12px;
    color: var(--accent);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .tools-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(28px, 3vw, 42px);
    line-height: 1.15;
    margin-bottom: 12px;
  }

  .tools-subtitle {
    color: var(--dim);
    font-size: 16px;
    line-height: 1.7;
    max-width: 760px;
  }

  .tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
  }

  .tool-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    transition: border-color 0.2s, transform 0.2s;
  }

  .tool-card:hover {
    border-color: rgba(79,142,247,0.4);
    transform: translateY(-2px);
  }

  .tool-icon {
    font-size: 24px;
    margin-bottom: 12px;
  }

  .tool-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px;
    margin-bottom: 8px;
  }

  .tool-desc {
    color: var(--dim);
    font-size: 14px;
    line-height: 1.7;
  }

  .tool-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }

  .tool-tag {
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(79,142,247,0.1);
    color: var(--accent);
    font-size: 12px;
    font-weight: 600;
  }

  .btn-secondary {
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
  }

  @media (max-width: 700px) {
    .tools-shell { padding: 20px 16px 60px; }
    .tools-hero { padding: 24px; }
    .tools-nav { flex-direction: column; align-items: flex-start; gap: 12px; }
  }
`;

const tools = [
  {
    title: "FHIR Resources",
    icon: "🧾",
    desc: "A toolkit for working with Patient, Observation, Condition, Encounter, MedicationRequest and more.",
    tags: ["FHIR", "Resources", "Validation"],
    path: "/tools/fhir",
  },
  {
    title: "HL7 Suite",
    icon: "📋",
    desc: "Convert between HL7 and FHIR, parse messages, validate structure, and inspect segments and fields.",
    tags: ["HL7", "FHIR", "Interoperability"],
    path: "/tools/hl7-suite",
  },
  {
    title: "Terminology Center",
    icon: "🏥",
    desc: "Search and browse medical terminology including SNOMED CT, ICD-10, LOINC, RxNorm, and FHIR ValueSets.",
    tags: ["Terminology", "SNOMED", "LOINC", "RxNorm"],
    path: "/tools/terminology",
  },
  {
    title: "API Documentation",
    icon: "🔌",
    desc: "Interactive API examples with code generation in cURL, Python, JavaScript, and Node.js.",
    tags: ["API", "Documentation", "Code"],
    path: "/tools/api",
  },
  {
    title: "Radiology Tools",
    icon: "🩻",
    desc: "Support for imaging studies, report mapping, and clinical data handling in radiology workflows.",
    tags: ["Radiology", "Imaging", "Reports"],
    path: null,
  },
  {
    title: "More tools coming",
    icon: "🚀",
    desc: "Lab, pharmacy, claims, mapping, and other healthcare data utilities can be added here.",
    tags: ["Roadmap", "Healthcare", "Future"],
    path: null,
  },
];

export default function ToolsPage() {
  const navigate = useNavigate();

  return (
    <div className="tools-page">
      <style>{styles}</style>
      <div className="tools-shell">
        <nav className="tools-nav">
          <div className="tools-brand" onClick={() => navigate('/')}>
            <div className="tools-brand-icon">M</div>
            <span>MedTechTools</span>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn-secondary" onClick={() => navigate('/api-key')}>Manage API</button>
            <button className="btn-secondary" onClick={() => navigate('/docs')}>View docs</button>
          </div>
        </nav>

        <section className="tools-hero">
          <div className="tools-eyebrow">Product vision</div>
          <h1 className="tools-title">One platform for healthcare data tools.</h1>
          <p className="tools-subtitle">
            The long-term goal is to become a growing toolbox for healthcare interoperability, where visitors can discover tools for FHIR resources, HL7 conversion, radiology workflows, and many more areas.
          </p>
        </section>

        <section className="tools-grid">
          {tools.map((tool) => (
            <div key={tool.title} className="tool-card" onClick={() => tool.path && navigate(tool.path)} style={{ cursor: tool.path ? "pointer" : "default" }}>
              <div className="tool-icon">{tool.icon}</div>
              <div className="tool-title">{tool.title}</div>
              <div className="tool-desc">{tool.desc}</div>
              <div className="tool-tags">
                {tool.tags.map((tag) => (
                  <span key={tag} className="tool-tag">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
