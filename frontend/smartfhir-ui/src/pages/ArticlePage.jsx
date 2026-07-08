import { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { articles } from "../content/docsContent";

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

  .article-page {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
  }

  .article-shell {
    max-width: 900px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }

  .article-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 28px;
  }

  .article-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 18px;
    cursor: pointer;
  }

  .article-brand-icon {
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

  .article-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 32px;
  }

  .article-eyebrow {
    display: inline-block;
    margin-bottom: 14px;
    color: var(--accent);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .article-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(28px, 3vw, 40px);
    line-height: 1.15;
    margin-bottom: 12px;
  }

  .article-summary {
    color: var(--dim);
    font-size: 16px;
    line-height: 1.7;
    margin-bottom: 20px;
  }

  .article-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 24px;
  }

  .article-tag {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(79,142,247,0.1);
    color: var(--accent);
    font-size: 12px;
    font-weight: 600;
  }

  .article-content {
    color: var(--text);
    line-height: 1.8;
    font-size: 15px;
  }

  .article-content p {
    margin-bottom: 14px;
  }

  .article-content h2 {
    margin-top: 24px;
    margin-bottom: 10px;
    font-size: 20px;
    font-family: 'Space Grotesk', sans-serif;
  }

  .article-content ul {
    padding-left: 18px;
    margin-bottom: 16px;
  }

  .article-back {
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text);
    border-radius: 10px;
    padding: 10px 14px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
  }

  @media (max-width: 700px) {
    .article-shell { padding: 20px 16px 60px; }
    .article-card { padding: 24px; }
    .article-nav { flex-direction: column; align-items: flex-start; gap: 12px; }
  }
`;

export default function ArticlePage() {
  const navigate = useNavigate();
  const { slug } = useParams();

  const article = useMemo(() => articles.find((item) => item.slug === slug), [slug]);

  if (!article) {
    return (
      <div className="article-page">
        <style>{styles}</style>
        <div className="article-shell">
          <div className="article-card">
            <div className="article-eyebrow">Article not found</div>
            <h1 className="article-title">This article is not available yet.</h1>
            <p className="article-summary">Please return to the docs page and choose another article.</p>
            <button className="article-back" onClick={() => navigate('/docs')}>Back to docs</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="article-page">
      <style>{styles}</style>
      <div className="article-shell">
        <nav className="article-nav">
          <div className="article-brand" onClick={() => navigate('/')}>
            <div className="article-brand-icon">M</div>
            <span>MedTechTools</span>
          </div>
          <button className="article-back" onClick={() => navigate('/docs')}>Back to docs</button>
        </nav>

        <article className="article-card">
          <div className="article-eyebrow">Article</div>
          <h1 className="article-title">{article.title}</h1>
          <p className="article-summary">{article.summary}</p>
          <div className="article-tags">
            {article.tags.map((tag) => (
              <span key={tag} className="article-tag">{tag}</span>
            ))}
          </div>
          <div className="article-content" dangerouslySetInnerHTML={{ __html: article.content }} />
        </article>
      </div>
    </div>
  );
}
