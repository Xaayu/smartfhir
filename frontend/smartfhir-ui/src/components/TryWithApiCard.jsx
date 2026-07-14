import { useState, useEffect } from "react";

const STORAGE_KEY = "smartfhirApiTab";

const TABS = [
  { id: "curl", label: "cURL" },
  { id: "python", label: "Python" },
  { id: "javascript", label: "JavaScript" },
  { id: "node", label: "Node.js" },
];

// Default code templates for each language
const DEFAULT_TEMPLATES = {
  curl: (endpoint, method, headers, body) => {
    const headerString = Object.entries(headers)
      .map(([key, value]) => `  -H "${key}: ${value}" \\`)
      .join('\n');
    
    const bodyString = body ? `  -d '${JSON.stringify(body, null, 2).replace(/\n/g, '\\n  ')}'` : '';
    
    return `curl -X ${method} "${endpoint}" \\
${headerString}${bodyString ? '\n' + bodyString : ''}`;
  },
  
  python: (endpoint, method, headers, body) => {
    const headerString = JSON.stringify(headers, null, 2);
    const bodyString = body ? `,\n    json=${JSON.stringify(body, null, 4)}` : '';
    
    return `import requests

url = "${endpoint}"
headers = ${headerString}
response = requests.${method.toLowerCase()}(url${bodyString}, headers=headers)

print(response.status_code)
print(response.json())`;
  },
  
  javascript: (endpoint, method, headers, body) => {
    const headerString = JSON.stringify(headers, null, 2);
    const bodyString = body ? `,\n  body: JSON.stringify(${JSON.stringify(body, null, 2)})` : '';
    
    return `fetch("${endpoint}", {
  method: "${method}",
  headers: ${headerString}${bodyString}
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));`;
  },
  
  node: (endpoint, method, headers, body) => {
    const headerString = JSON.stringify(headers, null, 2);
    
    return `const https = require('https');

const options = {
  hostname: new URL("${endpoint}").hostname,
  port: 443,
  path: new URL("${endpoint}").pathname,
  method: "${method}",
  headers: ${headerString}
};

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => { console.log(JSON.parse(data)); });
});

${body ? `req.write(JSON.stringify(${JSON.stringify(body, null, 2)}));` : ''}
req.end();`;
  },
};

function TryWithApiCard({ 
  endpoint = "https://api.example.com/v1/resource",
  method = "GET",
  headers = {},
  body = null,
  colors,
  customTemplates = {}
}) {
  const [activeTab, setActiveTab] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved && TABS.find(tab => tab.id === saved) ? saved : "curl";
  });
  const [copied, setCopied] = useState(false);

  // Update localStorage when tab changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, activeTab);
  }, [activeTab]);

  // Merge custom templates with defaults
  const templates = { ...DEFAULT_TEMPLATES, ...customTemplates };

  // Generate code for current tab
  const generateCode = () => {
    const template = templates[activeTab] || DEFAULT_TEMPLATES[activeTab];
    return template(endpoint, method, headers, body);
  };

  const handleCopy = async () => {
    const code = generateCode();
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div style={{
      background: colors.surface,
      border: `1px solid ${colors.border}`,
      borderRadius: 12,
      overflow: "hidden",
      boxShadow: `0 4px 20px ${colors.shadow}`,
    }}>
      {/* Header with tabs and copy button */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 16px",
        borderBottom: `1px solid ${colors.border}`,
        background: colors.bg,
      }}>
        {/* Tabs */}
        <div style={{ display: "flex", gap: 4 }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "6px 12px",
                borderRadius: 6,
                border: "none",
                background: activeTab === tab.id ? colors.accent : "transparent",
                color: activeTab === tab.id ? "#fff" : colors.textDim,
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                if (activeTab !== tab.id) {
                  e.currentTarget.style.background = colors.border;
                }
              }}
              onMouseLeave={(e) => {
                if (activeTab !== tab.id) {
                  e.currentTarget.style.background = "transparent";
                }
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Copy button */}
        <button
          onClick={handleCopy}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "6px 12px",
            borderRadius: 6,
            border: `1px solid ${colors.border}`,
            background: colors.surface,
            color: colors.text,
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = colors.border;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = colors.surface;
          }}
        >
          {copied ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Copy Code
            </>
          )}
        </button>
      </div>

      {/* Code block */}
      <div style={{
        position: "relative",
        background: colors.bg,
        padding: "16px",
        overflow: "auto",
      }}>
        <pre style={{
          margin: 0,
          fontFamily: "'Fira Code', 'Monaco', 'Consolas', monospace",
          fontSize: 13,
          lineHeight: 1.6,
          color: colors.text,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}>
          {generateCode()}
        </pre>
      </div>
    </div>
  );
}

export default TryWithApiCard;