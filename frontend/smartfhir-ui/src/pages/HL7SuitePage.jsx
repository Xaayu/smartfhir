import { useMemo, useState } from "react";
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
  .hl7-page { min-height: 100vh; background: var(--bg); color: var(--text); font-family: Inter, Arial, sans-serif; }
  .hl7-shell { max-width: 1200px; margin: 0 auto; padding: 28px 20px 64px; }
  .hl7-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
  .hl7-brand { display: flex; align-items: center; gap: 10px; font-weight: 800; cursor: pointer; }
  .hl7-brand-icon { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 10px; background: linear-gradient(135deg, var(--accent), var(--teal)); }
  .hl7-header { background: linear-gradient(135deg, rgba(79,142,247,0.2), rgba(38,201,160,0.12)); border: 1px solid var(--border); border-radius: 24px; padding: 28px; margin-bottom: 20px; }
  .hl7-title { font-size: 28px; font-weight: 800; margin: 0 0 10px; }
  .hl7-subtitle { color: var(--muted); max-width: 780px; line-height: 1.6; }
  .hl7-grid { display: grid; gap: 16px; }
  .hl7-card { background: var(--surface); border: 1px solid var(--border); border-radius: 18px; padding: 18px; }
  .hl7-card h3 { margin: 0 0 8px; font-size: 18px; }
  .hl7-card p { color: var(--muted); line-height: 1.5; margin: 0 0 12px; }
  .hl7-input, .hl7-select { width: 100%; border: 1px solid var(--border); background: var(--surface-2); color: var(--text); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; font: inherit; }
  .hl7-textarea { width: 100%; min-height: 170px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; font-family: ui-monospace, monospace; resize: vertical; }
  .hl7-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 6px; }
  .hl7-btn { border: none; border-radius: 10px; padding: 10px 14px; cursor: pointer; font-weight: 700; background: linear-gradient(135deg, var(--accent), var(--teal)); color: #fff; }
  .hl7-btn.secondary { background: transparent; color: var(--text); border: 1px solid var(--border); }
  .hl7-output { margin-top: 10px; padding: 12px; border-radius: 10px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); white-space: pre-wrap; font-family: ui-monospace, monospace; font-size: 13px; color: var(--muted); overflow: auto; }
  .hl7-inline { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
  @media (max-width: 700px) { .hl7-shell { padding: 18px 14px 48px; } .hl7-header { padding: 20px; } }
`;

const defaultHl7 = `MSH|^~\\&|ADT1|MCM|LABADT|MCM|202401011200||ADT^A01|MSG00001|P|2.5\r\nPID|1||12345||Doe^John`;
const defaultFhir = JSON.stringify({
  resourceType: "Patient",
  id: "P123",
  name: [{ family: "Doe", given: ["John"] }],
  gender: "male",
  birthDate: "1990-01-01"
}, null, 2);

function HL7SuitePage() {
  const navigate = useNavigate();
  const [hl7Input, setHl7Input] = useState(defaultHl7);
  const [fhirInput, setFhirInput] = useState(defaultFhir);
  const [hl7ToFhirResult, setHl7ToFhirResult] = useState("");
  const [fhirToHl7Result, setFhirToHl7Result] = useState("");
  const [parserResult, setParserResult] = useState("");
  const [validatorResult, setValidatorResult] = useState("");
  const [segmentId, setSegmentId] = useState("PID");
  const [fieldIndex, setFieldIndex] = useState(2);
  const [componentIndex, setComponentIndex] = useState(0);
  const [explorerResult, setExplorerResult] = useState("");

  const toolList = useMemo(() => [
    { title: "HL7 → FHIR", desc: "Convert an HL7 v2 message into a FHIR bundle output." },
    { title: "FHIR → HL7", desc: "Create a simple HL7 message from a FHIR resource." },
    { title: "HL7 Parser", desc: "Parse HL7 segments and inspect fields." },
    { title: "HL7 Validator", desc: "Check the basic structure of your HL7 message." },
    { title: "Segment & Field Explorer", desc: "Inspect a selected segment and field in detail." },
  ], []);

  async function runHl7ToFhir() {
    setHl7ToFhirResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7-to-fhir`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hl7_message: hl7Input, explain_errors: true }),
      });
      const data = await res.json();
      setHl7ToFhirResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setHl7ToFhirResult(`Error: ${error.message}`);
    }
  }

  async function runFhirToHl7() {
    setFhirToHl7Result("Running...");
    try {
      const resource = JSON.parse(fhirInput);
      const res = await fetch(`${API_BASE}/api/fhir-to-hl7`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resource }),
      });
      const data = await res.json();
      setFhirToHl7Result(JSON.stringify(data, null, 2));
    } catch (error) {
      setFhirToHl7Result(`Error: ${error.message}`);
    }
  }

  async function runParser() {
    setParserResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hl7_message: hl7Input }),
      });
      const data = await res.json();
      setParserResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setParserResult(`Error: ${error.message}`);
    }
  }

  async function runValidator() {
    setValidatorResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hl7_message: hl7Input }),
      });
      const data = await res.json();
      setValidatorResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setValidatorResult(`Error: ${error.message}`);
    }
  }

  async function runExplorer() {
    setExplorerResult("Running...");
    try {
      const res = await fetch(`${API_BASE}/api/hl7/segment-explorer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hl7_message: hl7Input,
          segment_id: segmentId,
          field_index: fieldIndex ? Number(fieldIndex) : null,
          component_index: componentIndex !== "" ? Number(componentIndex) : null,
        }),
      });
      const data = await res.json();
      setExplorerResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setExplorerResult(`Error: ${error.message}`);
    }
  }

  return (
    <div className="hl7-page">
      <style>{styles}</style>
      <div className="hl7-shell">
        <nav className="hl7-nav">
          <div className="hl7-brand" onClick={() => navigate("/")}>
            <div className="hl7-brand-icon">M</div>
            <span>MedTechTools</span>
          </div>
          <button className="hl7-btn secondary" onClick={() => navigate("/tools")}>Back to tools</button>
        </nav>

        <section className="hl7-header">
          <h1 className="hl7-title">HL7 Suite</h1>
          <p className="hl7-subtitle">
            Work with HL7 v2 messages end to end: convert them, parse them, validate them, and inspect segments and fields in a developer-friendly workspace.
          </p>
        </section>

        <section className="hl7-grid">
          <div className="hl7-card">
            <h3>Available tools</h3>
            <p>These are the first HL7 tools now available in the product.</p>
            <div className="hl7-grid">
              {toolList.map((tool) => (
                <div key={tool.title} className="hl7-card" style={{ padding: 14 }}>
                  <strong>{tool.title}</strong>
                  <p style={{ marginTop: 6 }}>{tool.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="hl7-card">
            <h3>HL7 → FHIR</h3>
            <p>Paste an HL7 message and transform it into a FHIR bundle response.</p>
            <textarea className="hl7-textarea" value={hl7Input} onChange={(e) => setHl7Input(e.target.value)} />
            <div className="hl7-actions">
              <button className="hl7-btn" onClick={runHl7ToFhir}>Convert</button>
            </div>
            <div className="hl7-output">{hl7ToFhirResult}</div>
          </div>

          <div className="hl7-card">
            <h3>FHIR → HL7</h3>
            <p>Paste a FHIR resource JSON and generate a simple HL7 message.</p>
            <textarea className="hl7-textarea" value={fhirInput} onChange={(e) => setFhirInput(e.target.value)} />
            <div className="hl7-actions">
              <button className="hl7-btn" onClick={runFhirToHl7}>Generate</button>
            </div>
            <div className="hl7-output">{fhirToHl7Result}</div>
          </div>

          <div className="hl7-card">
            <h3>HL7 Parser</h3>
            <p>Break the HL7 message into structured segments and fields.</p>
            <textarea className="hl7-textarea" value={hl7Input} onChange={(e) => setHl7Input(e.target.value)} />
            <div className="hl7-actions">
              <button className="hl7-btn" onClick={runParser}>Parse</button>
            </div>
            <div className="hl7-output">{parserResult}</div>
          </div>

          <div className="hl7-card">
            <h3>HL7 Validator</h3>
            <p>Validate the message structure and see any issues immediately.</p>
            <textarea className="hl7-textarea" value={hl7Input} onChange={(e) => setHl7Input(e.target.value)} />
            <div className="hl7-actions">
              <button className="hl7-btn" onClick={runValidator}>Validate</button>
            </div>
            <div className="hl7-output">{validatorResult}</div>
          </div>

          <div className="hl7-card">
            <h3>Segment & Field Explorer</h3>
            <p>Inspect a specific segment and field value from the HL7 message.</p>
            <textarea className="hl7-textarea" value={hl7Input} onChange={(e) => setHl7Input(e.target.value)} />
            <div className="hl7-inline">
              <input className="hl7-input" value={segmentId} onChange={(e) => setSegmentId(e.target.value)} placeholder="Segment ID" />
              <input className="hl7-input" type="number" value={fieldIndex} onChange={(e) => setFieldIndex(e.target.value)} placeholder="Field index" />
              <input className="hl7-input" type="number" value={componentIndex} onChange={(e) => setComponentIndex(e.target.value)} placeholder="Component index" />
            </div>
            <div className="hl7-actions">
              <button className="hl7-btn" onClick={runExplorer}>Explore</button>
            </div>
            <div className="hl7-output">{explorerResult}</div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default HL7SuitePage;
