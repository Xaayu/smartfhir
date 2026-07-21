import { useNavigate } from "react-router-dom";
import { articles, faqs } from "../content/docsContent";
import MedTechLogo from "../components/MedTechLogo";

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

  * { box-sizing: border-box; }
  body { margin: 0; }

  /* Custom scrollbar styling */
  ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }
  ::-webkit-scrollbar-track {
    background: var(--bg);
  }
  ::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 5px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: var(--accent);
  }

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

  .docs-page {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
  }

  .docs-shell {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }

  .docs-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0 32px;
  }

  .docs-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 18px;
    cursor: pointer;
  }

  .docs-brand-icon {
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

  .docs-hero {
    background: linear-gradient(135deg, rgba(79,142,247,0.14), rgba(0,212,170,0.08));
    border: 1px solid rgba(79,142,247,0.2);
    border-radius: 24px;
    padding: 36px;
    margin-bottom: 24px;
  }

  .docs-eyebrow {
    display: inline-block;
    margin-bottom: 12px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
  }

  .docs-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(28px, 3vw, 42px);
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 12px;
  }

  .docs-subtitle {
    font-size: 16px;
    line-height: 1.7;
    color: var(--dim);
    max-width: 720px;
  }

  .docs-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 24px;
  }

  .btn-primary, .btn-secondary {
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
  }

  .btn-primary {
    border: none;
    background: var(--accent);
    color: #fff;
  }

  .btn-secondary {
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border);
  }

  .docs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-top: 24px;
  }

  .docs-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px;
  }

  .docs-card h3 {
    margin: 0 0 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px;
  }

  .docs-card p {
    margin: 0;
    color: var(--dim);
    line-height: 1.7;
    font-size: 14px;
  }

  .docs-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }

  .docs-chip {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(79,142,247,0.1);
    color: var(--accent);
    font-size: 12px;
    font-weight: 600;
  }

  .faq-list {
    display: grid;
    gap: 12px;
    margin-top: 16px;
  }

  .faq-item {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
  }

  .faq-item strong {
    display: block;
    margin-bottom: 6px;
    color: var(--text);
  }

  .faq-item span {
    color: var(--dim);
    font-size: 14px;
    line-height: 1.6;
  }

  @media (max-width: 700px) {
    .docs-shell { padding: 20px 16px 60px; }
    .docs-hero { padding: 24px; }
    .docs-nav { flex-direction: column; align-items: flex-start; gap: 12px; }
  }
`;

export default function DocsPage() {
  const navigate = useNavigate();

  return (
    <div className="docs-page">
      <style>{styles}</style>
      <div className="docs-shell">
        <nav className="docs-nav">
          <div className="docs-brand" onClick={() => navigate('/')}>
            <MedTechLogo size={32} />
            <span>MedTechTools</span>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn-secondary" onClick={() => navigate('/tools/api')}>
              API Docs
            </button>
            <button className="btn-secondary" onClick={() => navigate('/api-key')}>
              Get API key
            </button>
          </div>
        </nav>

        <section className="docs-hero">
          <div className="docs-eyebrow">Docs & resources</div>
          <h1 className="docs-title">Everything you need to understand, try, and adopt MedTechTools.</h1>
          <p className="docs-subtitle">
            Explore quick-start guides, articles, FAQs, and future blog posts in one place. This section is designed to grow with your product and improve trust for new visitors.
          </p>
          <div className="docs-actions">
            <button className="btn-primary" onClick={() => navigate('/api-key')}>Start now</button>
            <button className="btn-secondary" onClick={() => navigate('/')}>Back to home</button>
          </div>
        </section>

        <section className="docs-grid">
          <div className="docs-card">
            <h3>Articles</h3>
            <p>Short, practical guides for setup, workflows, and common FHIR issues.</p>
          </div>
          <div className="docs-card">
            <h3>FAQ</h3>
            <p>Fast answers for common questions about use cases, features, and integration.</p>
          </div>
          <div className="docs-card">
            <h3>Blog updates</h3>
            <p>Product notes, launch updates, and lessons from building healthcare data tools.</p>
          </div>
        </section>

        <section className="docs-grid" style={{ marginTop: 24 }}>
          {articles.map((article) => (
            <div key={article.title} className="docs-card" style={{ cursor: 'pointer' }} onClick={() => navigate(`/docs/${article.slug}`)}>
              <h3>{article.title}</h3>
              <p>{article.desc}</p>
              <div className="docs-chip-row">
                {article.tags.map((tag) => (
                  <span key={tag} className="docs-chip">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </section>

        <section className="docs-card" style={{ marginTop: 24 }}>
          <h3>Frequently asked questions</h3>
          <div className="faq-list">
            {faqs.map((faq) => (
              <div key={faq.question} className="faq-item">
                <strong>{faq.question}</strong>
                <span>{faq.answer}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
