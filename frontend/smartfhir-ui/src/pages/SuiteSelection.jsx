import { useNavigate } from "react-router-dom";

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap');

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

  .suite-selection-page {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
  }

  .suite-shell {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 16px 80px;
  }

  @media (max-width: 700px) {
    .suite-shell { padding: 20px 16px 60px; }
    .suite-nav { flex-direction: column; align-items: flex-start; gap: 12px; }
  }

  .suite-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
  }

  .suite-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 18px;
    cursor: pointer;
  }

  .suite-brand-icon {
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

  .suite-hero {
    text-align: center;
    margin-bottom: 48px;
  }

  .suite-eyebrow {
    display: inline-block;
    margin-bottom: 12px;
    color: var(--accent);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .suite-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(32px, 4vw, 48px);
    line-height: 1.15;
    margin-bottom: 12px;
  }

  .suite-subtitle {
    color: var(--dim);
    font-size: 16px;
    line-height: 1.7;
    max-width: 600px;
    margin: 0 auto;
  }

  .suite-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
  }

  .suite-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 32px;
    transition: all 0.3s ease;
    cursor: pointer;
    display: flex;
    flex-direction: column;
  }

  .suite-card:hover {
    border-color: rgba(79,142,247,0.4);
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(79,142,247,0.15);
  }

  .suite-icon {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin-bottom: 20px;
  }

  .suite-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 12px;
  }

  .suite-description {
    color: var(--dim);
    font-size: 15px;
    line-height: 1.7;
    margin-bottom: 20px;
    flex: 1;
  }

  .suite-features {
    list-style: none;
    padding: 0;
    margin: 0 0 20px;
  }

  .suite-features li {
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .suite-features li::before {
    content: '✓';
    color: var(--teal);
    font-weight: 700;
  }

  .suite-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 100px;
    background: rgba(79,142,247,0.1);
    color: var(--accent);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
  }

  .suite-coming-soon {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 100px;
    background: rgba(148,163,184,0.15);
    color: var(--dim);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .suite-card.coming-soon {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .suite-card.coming-soon:hover {
    transform: none;
    box-shadow: none;
    border-color: var(--border);
  }

  .btn-secondary {
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s ease;
  }

  .btn-secondary:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  @media (max-width: 700px) {
    .suite-shell { padding: 20px 16px 60px; }
    .suite-nav { flex-direction: column; align-items: flex-start; gap: 12px; }
    .suite-grid { grid-template-columns: 1fr; }
  }
`;

const suites = [
  {
    id: 'fhir',
    name: 'FHIR Tools',
    icon: '🏥',
    iconBg: 'rgba(79,142,247,0.15)',
    description: 'Validate, explain, and auto-fix FHIR resources with intelligent field mapping and quality scoring.',
    features: [
      'Resource validation & auto-fix',
      'Smart field mapping',
      'Bundle generation',
      'Quality scoring (A-D grades)',
    ],
    path: '/tools/fhir',
  },
  {
    id: 'hl7',
    name: 'HL7 Suite',
    icon: '📨',
    iconBg: 'rgba(0,212,170,0.15)',
    description: 'Parse, validate, and convert HL7 v2 messages with detailed segment and field analysis.',
    features: [
      'HL7 v2 message parsing',
      'Segment validation',
      'Field mapping & extraction',
      'Message structure analysis',
    ],
    path: '/tools/hl7-suite',
  },
  {
    id: 'terminology',
    name: 'Terminology Suite',
    icon: '🔬',
    iconBg: 'rgba(251,191,36,0.15)',
    description: 'Lookup medical codes across LOINC, SNOMED CT, RxNorm, ICD-10, and more with live API fallback.',
    features: [
      'LOINC lab codes',
      'SNOMED CT diagnoses',
      'RxNorm medications',
      'ICD-10 conditions',
    ],
    path: '/tools/terminology',
  },
  {
    id: 'clinical-docs',
    name: 'Clinical Documents',
    icon: '📄',
    iconBg: 'rgba(148,163,184,0.15)',
    description: 'Generate, validate, and transform clinical documents including CCD, CDA, and structured care summaries.',
    features: [
      'CCD/CDA document generation',
      'Clinical note parsing',
      'Care summary creation',
      'Document validation',
    ],
    comingSoon: true,
  },
  {
    id: 'radiology',
    name: 'Radiology Tools',
    icon: '🔍',
    iconBg: 'rgba(148,163,184,0.15)',
    description: 'Work with DICOM imaging data, radiology reports, and imaging study metadata.',
    features: [
      'DICOM metadata parsing',
      'Radiology report analysis',
      'Imaging study management',
      'Modality-specific tools',
    ],
    comingSoon: true,
  },
  {
    id: 'laboratory',
    name: 'Laboratory Suite',
    icon: '🧪',
    iconBg: 'rgba(148,163,184,0.15)',
    description: 'Process lab orders, results, and reference ranges with comprehensive laboratory data management.',
    features: [
      'Lab order management',
      'Result interpretation',
      'Reference range validation',
      'LOINC mapping',
    ],
    comingSoon: true,
  },
  {
    id: 'pharmacy',
    name: 'Pharmacy Tools',
    icon: '💊',
    iconBg: 'rgba(148,163,184,0.15)',
    description: 'Manage prescriptions, medication interactions, and pharmacy dispensing workflows.',
    features: [
      'Prescription validation',
      'Drug interaction checks',
      'Medication reconciliation',
      'Dispensing workflow support',
    ],
    comingSoon: true,
  },
];

export default function SuiteSelection() {
  const navigate = useNavigate();

  return (
    <div className="suite-selection-page">
      <style>{styles}</style>
      <div className="suite-shell">
        <nav className="suite-nav">
          <div className="suite-brand" onClick={() => navigate('/')}>
            <div className="suite-brand-icon">M</div>
            <span>MedTechTools</span>
          </div>
          <button className="btn-secondary" onClick={() => navigate('/docs')}>View docs</button>
        </nav>

        <div className="suite-hero">
          <div className="suite-eyebrow">Developer Platform</div>
          <h1 className="suite-title">MedTechTools</h1>
          <p className="suite-subtitle">
            Developers Platform for Healthcare Interoperability. Build, validate, and transform healthcare data with powerful tools designed for modern health tech development.
          </p>
        </div>

        <div className="suite-grid">
          {suites.map((suite) => (
            <div 
              key={suite.id} 
              className={`suite-card ${suite.comingSoon ? 'coming-soon' : ''}`} 
              onClick={!suite.comingSoon ? () => navigate(suite.path) : undefined}
            >
              <div className="suite-icon" style={{ background: suite.iconBg }}>
                {suite.icon}
              </div>
              <div className="suite-name">{suite.name}</div>
              <div className="suite-description">{suite.description}</div>
              <ul className="suite-features">
                {suite.features.map((feature) => (
                  <li key={feature}>{feature}</li>
                ))}
              </ul>
              {suite.comingSoon ? (
                <div className="suite-coming-soon">Coming Soon</div>
              ) : (
                <div className="suite-badge">Open Suite →</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
