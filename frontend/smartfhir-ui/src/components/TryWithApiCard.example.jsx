import TryWithApiCard from "./TryWithApiCard";

// Example 1: Basic usage with default props
function BasicExample({ colors }) {
  return (
    <TryWithApiCard
      endpoint="https://api.smartfhir.com/v1/patient"
      method="POST"
      headers={{
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key-here"
      }}
      body={{
        resourceType: "Patient",
        name: [{ family: "Doe", given: ["John"] }],
        gender: "male",
        birthDate: "1990-04-15"
      }}
      colors={colors}
    />
  );
}

// Example 2: Dynamic with state
function DynamicExample({ colors }) {
  const [selectedResource, setSelectedResource] = useState("Patient");
  
  const endpoints = {
    Patient: "https://api.smartfhir.com/v1/patient",
    Observation: "https://api.smartfhir.com/v1/observation",
    Condition: "https://api.smartfhir.com/v1/condition"
  };

  return (
    <div>
      <select 
        value={selectedResource}
        onChange={(e) => setSelectedResource(e.target.value)}
        style={{ marginBottom: 16, padding: 8 }}
      >
        <option value="Patient">Patient</option>
        <option value="Observation">Observation</option>
        <option value="Condition">Condition</option>
      </select>
      
      <TryWithApiCard
        endpoint={endpoints[selectedResource]}
        method="POST"
        headers={{
          "Content-Type": "application/json",
          "X-API-Key": localStorage.getItem("smartfhirApiKey") || "your-api-key"
        }}
        body={{
          resourceType: selectedResource,
          // Add resource-specific fields
        }}
        colors={colors}
      />
    </div>
  );
}

// Example 3: Custom code template
function CustomTemplateExample({ colors }) {
  const customTemplates = {
    python: (endpoint, method, headers, body) => {
      return `# Custom Python template
import smartfhir

client = smartfhir.Client(api_key="${headers["X-API-Key"]}")

result = client.${method.toLowerCase()}("${endpoint}", ${
  body ? JSON.stringify(body, null, 6) : '{}'
})

print(result)`;
    }
  };

  return (
    <TryWithApiCard
      endpoint="https://api.smartfhir.com/v1/patient"
      method="POST"
      headers={{ "X-API-Key": "your-api-key" }}
      body={{ resourceType: "Patient" }}
      colors={colors}
      customTemplates={customTemplates}
    />
  );
}