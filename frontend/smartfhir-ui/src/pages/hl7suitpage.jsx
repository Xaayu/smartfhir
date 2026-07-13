import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";

const styles = `
  * { box-sizing: border-box; }
  body { margin: 0; }
  :root {
    --bg: #071119;
    --surface: #101b27;
    --surface-2: #162533;
    --border: #243447;
    --text: #f3f7fb;
    --muted: #95a8bf;
    --accent: #4f8ef7;
    --teal: #26c9a0;
  }
  .hl7-page.light {
    --bg: #f8fafc;
    --surface: #ffffff;
    --surface-2: #f1f5f9;
    --border: #e2e8f0;
    --text: #0f172a;
    --muted: #64748b;
    --accent: #3b82f6;
    --teal: #059669;
  }
  .hl7-page { min-height: 100vh; background: var(--bg); color: var(--text); font-family: Inter, Arial, sans-serif; transition: background 0.3s, color 0.3s; }
  .hl7-shell { max-width: 1600px; margin: 0 auto; padding: 22px 20px 64px; }

  .hl7-topbar { position: sticky; top: 0; z-index: 100; background: var(--bg); display: flex; justify-content: space-between; align-items: center; padding: 22px 0 18px 0; margin: -22px 0 20px 0; border-bottom: 1px solid var(--border); transition: background 0.3s; }
  .hl7-topbar-title { font-size: 18px; font-weight: 800; margin: 0 0 4px; }
  .hl7-topbar-sub { color: var(--muted); font-size: 13px; margin: 0; }
  .hl7-topbar-right { display: flex; align-items: center; gap: 10px; }
  .hl7-back-btn { border: 1px solid var(--border); background: transparent; color: var(--text); border-radius: 10px; padding: 8px 12px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .hl7-back-btn:hover { background: var(--surface-2); }
  .hl7-logout-btn { border: 1px solid #ef4444; background: transparent; color: #ef4444; border-radius: 10px; padding: 8px 12px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .hl7-logout-btn:hover { background: rgba(239, 68, 68, 0.1); }
  .hl7-icon-btn { width: 34px; height: 34px; border-radius: 10px; border: 1px solid var(--border); display: grid; place-items: center; background: transparent; color: var(--text); cursor: pointer; transition: all 0.2s; }
  .hl7-icon-btn:hover { background: var(--surface-2); }

  /* Redesigned classic tab deck */
  .hl7-tabs { display: flex; gap: 0; flex-wrap: wrap; border-bottom: 2px solid var(--border); margin-bottom: 20px; }
  .hl7-tab { background: transparent; color: var(--muted); border: none; border-bottom: 3px solid transparent; border-radius: 0; padding: 12px 24px; font-weight: 700; font-size: 15px; cursor: pointer; white-space: nowrap; margin-bottom: -2px; transition: all 0.2s; }
  .hl7-tab:hover { color: var(--text); }
  .hl7-tab.active { color: var(--accent); border-bottom-color: var(--accent); }

  .hl7-subtabs { display: flex; gap: 8px; margin-bottom: 14px; }
  .hl7-subtab { border: 1px solid var(--border); background: transparent; color: var(--muted); border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 700; letter-spacing: 0.02em; cursor: pointer; transition: all 0.2s; }
  .hl7-subtab:hover { border-color: var(--muted); color: var(--text); }
  .hl7-subtab.active { background: var(--surface-2); color: var(--text); border-color: var(--accent); }

  .hl7-toggle-switch { display: inline-flex; background: var(--surface-2); border-radius: 50px; padding: 4px; border: 1px solid var(--border); margin-bottom: 14px; }
  .hl7-toggle-btn { background: transparent; color: var(--muted); border: none; border-radius: 40px; padding: 8px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
  .hl7-toggle-btn.active { background: linear-gradient(135deg, var(--accent), var(--teal)); color: #06111c; box-shadow: 0 2px 10px rgba(38,201,160,0.2); }

  .hl7-workspace { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: stretch; }
  @media (max-width: 860px) { .hl7-workspace { grid-template-columns: 1fr; } }

  .hl7-card { background: var(--surface); border: 1px solid var(--border); border-radius: 18px; padding: 20px; display: flex; flex-direction: column; }
  .hl7-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .hl7-label { color: var(--muted); font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin: 0; }

  .hl7-textarea { flex-grow: 1; width: 100%; height: 400px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text); border-radius: 10px; padding: 14px; font-family: ui-monospace, monospace; font-size: 13px; line-height: 1.5; resize: none; overflow-y: auto; }
  .hl7-input { border: 1px solid var(--border); background: var(--surface-2); color: var(--text); border-radius: 10px; padding: 10px 12px; font: inherit; font-size: 13px; }
  .hl7-inline { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 12px; }

  .hl7-actions-center { display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px 0; }
  .hl7-run-btn { border: none; border-radius: 10px; padding: 16px 28px; cursor: pointer; font-weight: 800; font-size: 15px; background: linear-gradient(135deg, var(--accent), var(--teal)); color: #06111c; box-shadow: 0 4px 20px rgba(38,201,160,0.25); transition: transform 0.2s, box-shadow 0.2s; white-space: nowrap; width: 100%; }
  .hl7-run-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(38,201,160,0.35); }
  .hl7-run-btn:disabled { opacity: 0.7; cursor: not-allowed; transform: none; box-shadow: none; }

  .hl7-output-empty { color: var(--muted); font-size: 14px; line-height: 1.6; height: 400px; display: flex; align-items: center; justify-content: center; text-align: center; }
  .hl7-output { height: 400px; padding: 14px; border-radius: 10px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); white-space: pre-wrap; font-family: ui-monospace, monospace; font-size: 13px; color: var(--text); overflow-y: auto; flex-grow: 1; }

  /* Toast Notifications */
  .toast-container {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 10px;
    pointer-events: none;
  }
  .toast-card {
    pointer-events: auto;
    min-width: 300px;
    max-width: 420px;
    padding: 14px 18px;
    background: rgba(16, 27, 39, 0.85);
    border: 1px solid var(--border);
    backdrop-filter: blur(16px);
    border-radius: 12px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    gap: 12px;
    transform: translateX(120%);
    animation: toast-slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    transition: all 0.3s ease;
  }
  @keyframes toast-slide-in {
    to { transform: translateX(0); }
  }
  .toast-card.success { border-left: 4px solid var(--teal); }
  .toast-card.error { border-left: 4px solid #ef4444; }
  .toast-card.info { border-left: 4px solid var(--accent); }
  .toast-card.loading { border-left: 4px solid #f59e0b; }
  .toast-icon { display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .toast-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid transparent;
    border-top-color: #f59e0b;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  .toast-message { font-size: 13px; font-weight: 600; color: var(--text); line-height: 1.4; flex-grow: 1; }
  .toast-close-btn {
    background: transparent;
    border: none;
    color: var(--muted);
    cursor: pointer;
    font-size: 18px;
    padding: 0 0 0 8px;
    display: flex;
    align-items: center;
  }
  .toast-close-btn:hover { color: var(--text); }
`;
const defaultHl7 = `MSH|^~\\&|ADT1|MCM|LABADT|MCM|202401011200||ADT^A01|MSG00001|P|2.5\r\nPID|1||12345||Doe^John||19800101|M\r\nPV1|1|I|2000^209^01|||001^ADMITTING|...`;
const defaultFhir = JSON.stringify({
  resourceType: "Patient",
  id: "P123",
  name: [{ family: "Doe", given: ["John"] }],
  gender: "male",
  birthDate: "1990-01-01"
}, null, 2);

const TABS = [
  { id: "convert", label: "Convert" },
  { id: "parse", label: "Parse" },
  { id: "validate", label: "Validate" },
  { id: "explore", label: "Explore" },
];

// Helper to map generic field names for the inspector UI
const getFieldLabel = (segment, index) => {
  if (segment === "PID") {
    const labels = ["", "Set ID", "Patient ID", "Patient Identifier List", "Alternate Patient ID", "Patient Name", "Mother's Maiden Name", "Date/Time of Birth", "Administrative Sex", "Patient Alias", "Race", "Patient Address"];
    return labels[index] || `${segment}-${index}`;
  }
  if (segment === "MSH") {
    const labels = ["", "Field Separator", "Encoding Characters", "Sending Application", "Sending Facility", "Receiving Application", "Receiving Facility", "Date/Time of Message", "Security", "Message Type", "Message Control ID", "Processing ID", "Version ID"];
    return labels[index] || `${segment}-${index}`;
  }
  return `${segment}-${index}`;
};

function HL7SuitePage() {
  const navigate = useNavigate();

  const getHeaders = () => {
    const apiKey = localStorage.getItem("smartfhirApiKey");
    return {
      "Content-Type": "application/json",
      ...(apiKey ? { "X-API-Key": apiKey } : {}),
    };
  };

  useEffect(() => {
    document.title = "HL7 Suite: Parse & Convert HL7 to FHIR | MedTechTools";
  }, []);

  const [theme, setTheme] = useState("dark");
  const [activeTab, setActiveTab] = useState("convert");
  const [convertDirection, setConvertDirection] = useState("hl7-to-fhir");

  const [hl7Input, setHl7Input] = useState("");
  const [fhirInput, setFhirInput] = useState("");

  const [hl7ToFhirResult, setHl7ToFhirResult] = useState("");
  const [fhirToHl7Result, setFhirToHl7Result] = useState("");
  const [parserResult, setParserResult] = useState("");
  const [validatorResult, setValidatorResult] = useState("");
  const [explorerResult, setExplorerResult] = useState("");

  const [segmentId, setSegmentId] = useState("PID");
  const [fieldIndex, setFieldIndex] = useState(2);
  const [componentIndex, setComponentIndex] = useState(0);

  const [loading, setLoading] = useState(false);
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = "info", id = Date.now()) => {
    setToasts((prev) => {
      const idx = prev.findIndex((t) => t.id === id);
      if (idx > -1) {
        const next = [...prev];
        next[idx] = { ...next[idx], message, type };
        return next;
      }
      return [...prev, { id, message, type }];
    });

    if (type !== "loading") {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    }
    return id;
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const getToastIcon = (type) => {
    switch (type) {
      case "loading":
        return <div className="toast-spinner" />;
      case "success":
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        );
      case "error":
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        );
      case "info":
      default:
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        );
    }
  };


  async function runHl7ToFhir() {
    const toastId = Date.now();
    addToast("Converting HL7 to FHIR...", "loading", toastId);
    setLoading(true);
    setHl7ToFhirResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7-to-fhir`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ hl7_message: hl7Input, explain_errors: true }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setHl7ToFhirResult(JSON.stringify(data, null, 2));
      addToast("Conversion completed successfully!", "success", toastId);
    } catch (error) {
      setHl7ToFhirResult(`Error: ${error.message}`);
      addToast(`Conversion failed: ${error.message}`, "error", toastId);
    } finally {
      setLoading(false);
    }
  }

  async function runFhirToHl7() {
    const toastId = Date.now();
    addToast("Generating HL7 from FHIR...", "loading", toastId);
    setLoading(true);
    setFhirToHl7Result("Running...");
    try {
      const resource = JSON.parse(fhirInput || defaultFhir);
      const res = await fetch(`${API_BASE}/api/fhir-to-hl7`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ resource }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setFhirToHl7Result(JSON.stringify(data, null, 2));
      addToast("HL7 generated successfully!", "success", toastId);
    } catch (error) {
      setFhirToHl7Result(`Error: ${error.message}`);
      addToast(`Generation failed: ${error.message}`, "error", toastId);
    } finally {
      setLoading(false);
    }
  }

  async function runParser() {
    const toastId = Date.now();
    addToast("Parsing HL7 message...", "loading", toastId);
    setLoading(true);
    setParserResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7/parse`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ hl7_message: hl7Input }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setParserResult(JSON.stringify(data, null, 2));
      addToast("HL7 parsed successfully!", "success", toastId);
    } catch (error) {
      setParserResult(`Error: ${error.message}`);
      addToast(`Parsing failed: ${error.message}`, "error", toastId);
    } finally {
      setLoading(false);
    }
  }

  async function runValidator() {
    const toastId = Date.now();
    addToast("Validating HL7 message...", "loading", toastId);
    setLoading(true);
    setValidatorResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7/validate`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ hl7_message: hl7Input }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setValidatorResult(JSON.stringify(data, null, 2));
      addToast("Validation completed!", "success", toastId);
    } catch (error) {
      setValidatorResult(`Error: ${error.message}`);
      addToast(`Validation failed: ${error.message}`, "error", toastId);
    } finally {
      setLoading(false);
    }
  }

  async function runExplorer() {
    const toastId = Date.now();
    addToast(`Exploring segment ${segmentId}...`, "loading", toastId);
    setLoading(true);
    setExplorerResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7/segment-explorer`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          hl7_message: hl7Input,
          segment_id: segmentId,
          field_index: fieldIndex ? Number(fieldIndex) : null,
          component_index: componentIndex !== "" ? Number(componentIndex) : null,
        }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setExplorerResult(JSON.stringify(data, null, 2));
      addToast("Segment query complete!", "success", toastId);
    } catch (error) {
      setExplorerResult(`Error: ${error.message}`);
      addToast(`Query failed: ${error.message}`, "error", toastId);
    } finally {
      setLoading(false);
    }
  }


  const view = useMemo(() => {
    if (activeTab === "convert") {
      if (convertDirection === "hl7-to-fhir") {
        return {
          leftLabel: "HL7 message",
          rightLabel: "FHIR output",
          value: hl7Input,
          onChange: setHl7Input,
          run: runHl7ToFhir,
          runLabel: "Run Conversion",
          result: hl7ToFhirResult,
          emptyText: "Run the converter to see the FHIR bundle output here.",
          isHl7: true
        };
      }
      return {
        leftLabel: "FHIR resource (JSON)",
        rightLabel: "HL7 output",
        value: fhirInput,
        onChange: setFhirInput,
        run: runFhirToHl7,
        runLabel: "Generate HL7",
        result: fhirToHl7Result,
        emptyText: "Run the converter to see the generated HL7 message here.",
        isHl7: false
      };
    }
    if (activeTab === "parse") {
      return {
        leftLabel: "HL7 message",
        rightLabel: "Segment Breakdowns",
        value: hl7Input,
        onChange: setHl7Input,
        run: runParser,
        runLabel: "Parse Message",
        result: parserResult,
        emptyText: "Parse the message to see structured segments and fields here.",
        isHl7: true
      };
    }
    if (activeTab === "validate") {
      return {
        leftLabel: "HL7 message",
        rightLabel: "Validation Output",
        value: hl7Input,
        onChange: setHl7Input,
        run: runValidator,
        runLabel: "Run Validation",
        result: validatorResult,
        emptyText: "Validate the message to see structural issues here.",
        isHl7: true
      };
    }
    return {
      leftLabel: "HL7 message",
      rightLabel: "Segment Breakdowns & Output",
      value: hl7Input,
      onChange: setHl7Input,
      run: runExplorer,
      runLabel: "Run Explorer",
      result: explorerResult,
      emptyText: "Choose a segment and field, then explore to see the value here.",
      isHl7: true
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    activeTab,
    convertDirection,
    hl7Input,
    fhirInput,
    hl7ToFhirResult,
    fhirToHl7Result,
    parserResult,
    validatorResult,
    explorerResult,
  ]);

  const toggleTheme = () => {
    setTheme(prev => (prev === "dark" ? "light" : "dark"));
  };

  const handleLogout = () => {
    localStorage.removeItem("smartfhirApiKey");
    localStorage.removeItem("smartfhirAdminToken");
    navigate("/");
  };

  const renderRightPanelContent = () => {
    if (activeTab === "parse" || activeTab === "explore") {
       if (view.result === "Running...") return <div className="hl7-output">Running...</div>;
       if (view.result && view.result.startsWith("Error")) return <div className="hl7-output">{view.result}</div>;
       
       // Show Segment Breakdown
       if (view.result || hl7Input) {
         const hl7ToParse = hl7Input || defaultHl7;
         const segments = hl7ToParse.split(/[\r\n]+/).filter(Boolean);
         return (
           <div className="hl7-output" style={{ padding: '0', background: 'transparent', border: 'none' }}>
             <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
               {segments.map((seg, i) => {
                 const parts = seg.split('|');
                 const segName = parts[0];
                 // Quick logic for MSH: the first separator is implicitly a field, so it behaves slightly differently, but standard split handles it ok for display
                 return (
                   <div key={i} style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
                     <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
                       <h4 style={{ margin: 0, color: 'var(--accent)', fontSize: '15px' }}>{segName} Segment</h4>
                     </div>
                     <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                       {parts.map((p, j) => {
                         if (j === 0) return null;
                         const label = getFieldLabel(segName, j);
                         return (
                           <div key={j} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', fontSize: '13px', paddingBottom: '8px', borderBottom: j < parts.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}>
                             <span style={{ color: 'var(--muted)', width: '150px', flexShrink: 0, fontWeight: 600 }}>{label}</span>
                             <span style={{ color: 'var(--text)', wordBreak: 'break-all' }}>
                               {p ? <span style={{ color: 'var(--teal)' }}>{p.replace(/\^/g, ' ^ ')}</span> : <span style={{ opacity: 0.3 }}>Empty</span>}
                             </span>
                           </div>
                         );
                       })}
                     </div>
                   </div>
                 );
               })}
             </div>
             {activeTab === "explore" && view.result && (
               <div style={{ marginTop: '20px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
                 <h4 style={{ margin: '0 0 12px', color: 'var(--accent)' }}>Explorer Result</h4>
                 <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: 'var(--text)', fontSize: '13px' }}>{view.result}</pre>
               </div>
             )}
             {activeTab === "parse" && view.result && (
                <div style={{ marginTop: '20px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
                  <h4 style={{ margin: '0 0 12px', color: 'var(--accent)' }}>API JSON Result</h4>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: 'var(--text)', fontSize: '13px' }}>{view.result}</pre>
                </div>
             )}
           </div>
         );
       }
    }

    if (activeTab === "validate") {
       if (view.result === "Running...") return <div className="hl7-output">Running...</div>;
       if (view.result && view.result.startsWith("Error")) return <div className="hl7-output">{view.result}</div>;
       
       if (view.result) {
         let parsedReport = null;
         try {
           parsedReport = JSON.parse(view.result);
         } catch {
           parsedReport = null;
         }

         return (
           <div className="hl7-output" style={{ padding: '0', background: 'transparent', border: 'none' }}>
             <div style={{ padding: '16px', background: 'var(--surface-2)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <h4 style={{ color: 'var(--accent)', margin: '0 0 16px', fontSize: '16px' }}>Conformity Report</h4>
                
                {parsedReport && Array.isArray(parsedReport.issues) ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {parsedReport.issues.map((issue, idx) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: issue.severity === 'error' ? '#ef4444' : '#f59e0b' }}>
                        {issue.severity === 'error' ? (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                        ) : (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                        )}
                        <span style={{ fontWeight: 600 }}>{issue.message}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                      <span style={{ fontWeight: 600 }}>Syntax Error: Missing MSH-9 (Message Type)</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f59e0b' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                      <span style={{ fontWeight: 600 }}>Warning: PID-3 (Patient Identifier List) is recommended but empty.</span>
                    </div>
                  </div>
                )}
                
                <pre style={{ marginTop: '20px', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', fontSize: '13px', color: 'var(--muted)', whiteSpace: 'pre-wrap' }}>
                  {view.result}
                </pre>
             </div>
           </div>
         );
       }
    }

    // Default view for Convert / Validate
    return view.result ? (
      <div className="hl7-output">{view.result}</div>
    ) : (
      <div className="hl7-output-empty">
        <p>{view.emptyText}</p>
      </div>
    );
  };

  return (
    <div className={`hl7-page ${theme}`}>
      <style>{styles}</style>
      <div className="hl7-shell">
        <div className="hl7-topbar">
          <div>
            <p className="hl7-topbar-title">HL7 Suite</p>
            <p className="hl7-topbar-sub">Convert, parse, validate, and explore HL7 messages in one workspace.</p>
          </div>
          <div className="hl7-topbar-right">
            <button className="hl7-icon-btn" onClick={toggleTheme} aria-label="Toggle Theme">
              {theme === "dark" ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
              )}
            </button>
            <button className="hl7-back-btn" onClick={() => navigate("/api-key")}>Manage API</button>
            <button className="hl7-back-btn" onClick={() => navigate("/tools")}>Back to tools</button>
            <button className="hl7-logout-btn" onClick={handleLogout}>Logout</button>
          </div>
        </div>

        <div className="hl7-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`hl7-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "convert" && (
          <div className="hl7-toggle-switch">
            <button
              className={`hl7-toggle-btn ${convertDirection === "hl7-to-fhir" ? "active" : ""}`}
              onClick={() => setConvertDirection("hl7-to-fhir")}
            >
              HL7 → FHIR
            </button>
            <button
              className={`hl7-toggle-btn ${convertDirection === "fhir-to-hl7" ? "active" : ""}`}
              onClick={() => setConvertDirection("fhir-to-hl7")}
            >
              FHIR → HL7
            </button>
          </div>
        )}

        <section className="hl7-workspace">
          <div className="hl7-card">
            <div className="hl7-card-header">
              <p className="hl7-label">{view.leftLabel}</p>
              {view.isHl7 && (
                <button 
                  className="hl7-subtab" 
                  style={{margin: 0, padding: '4px 10px'}} 
                  onClick={() => view.onChange(defaultHl7)}
                >
                  Load Sample ADT^A01 Message
                </button>
              )}
            </div>
            <textarea
              className="hl7-textarea"
              value={view.value}
              onChange={(e) => view.onChange(e.target.value)}
              spellCheck={false}
              placeholder={view.isHl7 ? "Paste your HL7 message here..." : "Paste your FHIR JSON here..."}
            />

            {activeTab === "explore" && (
              <div className="hl7-inline">
                <input
                  className="hl7-input"
                  value={segmentId}
                  onChange={(e) => setSegmentId(e.target.value)}
                  placeholder="Segment ID (e.g. PID)"
                />
                <input
                  className="hl7-input"
                  type="number"
                  value={fieldIndex}
                  onChange={(e) => setFieldIndex(e.target.value)}
                  placeholder="Field index"
                />
                <input
                  className="hl7-input"
                  type="number"
                  value={componentIndex}
                  onChange={(e) => setComponentIndex(e.target.value)}
                  placeholder="Component index"
                />
              </div>
            )}

            <div style={{ marginTop: '16px' }}>
               <button className="hl7-run-btn" onClick={view.run} disabled={loading}>
                 {view.runLabel}
               </button>
            </div>
          </div>

          <div className="hl7-card">
            <div className="hl7-card-header">
              <p className="hl7-label">{view.rightLabel}</p>
            </div>
            {renderRightPanelContent()}
          </div>
        </section>

        {/* Toast Notifications */}
        <div className="toast-container">
          {toasts.map((toast) => (
            <div key={toast.id} className={`toast-card ${toast.type}`}>
              <div className="toast-icon">
                {getToastIcon(toast.type)}
              </div>
              <div className="toast-message">{toast.message}</div>
              <button className="toast-close-btn" aria-label="Close notification" onClick={() => removeToast(toast.id)}>
                &times;
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default HL7SuitePage;