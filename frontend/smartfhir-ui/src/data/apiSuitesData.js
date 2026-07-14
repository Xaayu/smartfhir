// API Suites Data Structure for Multi-Suite API Playground
// Contains all three suites: FHIR Resources, HL7 Suite, and Terminology Center

export const API_SUITES = {
  fhir: {
    id: "fhir",
    name: "FHIR Resources",
    description: "Validate and transform FHIR healthcare data",
    icon: "📋",
    color: "#4F8EF7",
    resources: [
      {
        id: "patient",
        name: "Patient",
        description: "Create and validate FHIR Patient resources",
        method: "POST",
        endpoint: "/api/v1/fhir/Patient/validate",
        body: {
          resourceType: "Patient",
          PtID: "P101",
          first_name: "John",
          last_name: "Doe",
          Sex: "M",
          DOB: "15/04/1990",
          marital: "married",
          language: "English",
          phone: "555-1234",
          email: "john@example.com",
        },
      },
      {
        id: "observation",
        name: "Observation",
        description: "Create and validate FHIR Observation resources",
        method: "POST",
        endpoint: "/api/v1/fhir/Observation/validate",
        body: {
          resourceType: "Observation",
          TestName: "Blood Pressure",
          Value: "120",
          Unit: "mmHg",
          PatientID: "P101",
          Date: "15/01/2024",
          Status: "final",
          Interpretation: "N",
        },
      },
      {
        id: "condition",
        name: "Condition",
        description: "Create and validate FHIR Condition resources",
        method: "POST",
        endpoint: "/api/v1/fhir/Condition/validate",
        body: {
          resourceType: "Condition",
          PatientID: "P101",
          Diagnosis: "Diabetes Type 2",
          Status: "ongoing",
          Severity: "serious",
          VerificationStatus: "yes",
          OnsetDate: "15/06/2023",
          RecordedDate: "20/06/2023",
          Note: "Patient on insulin therapy",
        },
      },
      {
        id: "encounter",
        name: "Encounter",
        description: "Create and validate FHIR Encounter resources",
        method: "POST",
        endpoint: "/api/v1/fhir/Encounter/validate",
        body: {
          resourceType: "Encounter",
          EncounterID: "E101",
          PatientID: "P101",
          Status: "in-progress",
          Class: "inpatient",
          Type: "Consultation",
          StartDate: "15/01/2024",
          EndDate: "16/01/2024",
        },
      },
      {
        id: "medication",
        name: "MedicationRequest",
        description: "Create and validate FHIR MedicationRequest resources",
        method: "POST",
        endpoint: "/api/v1/fhir/MedicationRequest/validate",
        body: {
          resourceType: "MedicationRequest",
          RequestID: "MR101",
          PatientID: "P101",
          Medication: "Metformin 500mg",
          Dosage: "1 tablet twice daily",
          Status: "active",
          Intent: "order",
          AuthoredOn: "15/01/2024",
        },
      },
    ],
  },
  hl7: {
    id: "hl7",
    name: "HL7 Suite",
    description: "Parse and convert HL7 v2 messages",
    icon: "📄",
    color: "#34D399",
    resources: [
      {
        id: "v2-to-fhir",
        name: "v2 to FHIR Converter",
        description: "Convert HL7 v2 messages to FHIR resources",
        method: "POST",
        endpoint: "/api/v1/hl7/v2-to-fhir",
        body: {
          hl7_message: "MSH|^~\\&|ADT|GOOD_HEALTH_HOSPITAL|GHH_LAB|ELAB-3|200604051730||ADT^A04|123456789|P|2.5|||AL||AL|USA|ASCII|8859/1\rPID|1||12345^^^GHH^MR||DOE^JOHN^A||19600101|M|||123 MAIN ST^^SPRINGFIELD^IL^62701||555-555-5555|||M||123456789|987654321|N",
          target_resource: "Patient",
        },
      },
      {
        id: "hl7-parser",
        name: "HL7 Parser",
        description: "Parse and analyze HL7 v2 message structure",
        method: "POST",
        endpoint: "/api/v1/hl7/parse",
        body: {
          hl7_message: "MSH|^~\\&|SENDING_APP|SENDING_FACILITY|RECEIVING_APP|RECEIVING_FACILITY|202401151200||ADT^A01|MSG001|P|2.5\rEVN|A01|202401151200||\rPID|1||PAT123^^^HOSPITAL^MR||DOE^JOHN||19700101|M|||123 STREET^CITY^STATE^12345||555-123-4567|||M||PAT123456789",
        },
      },
      {
        id: "segment-inspector",
        name: "Segment Inspector",
        description: "Inspect and validate specific HL7 segments",
        method: "POST",
        endpoint: "/api/v1/hl7/inspect-segment",
        body: {
          hl7_message: "MSH|^~\\&|APP|FACILITY|RECEIVER|LOCATION|202401151200||ADT^A01|MSG001|P|2.5\rPID|1||PAT123||DOE^JOHN||19700101|M",
          segment_type: "PID",
        },
      },
    ],
  },
  terminology: {
    id: "terminology",
    name: "Terminology Center",
    description: "Search and map medical terminologies",
    icon: "📚",
    color: "#A855F7",
    resources: [
      {
        id: "snomed-search",
        name: "SNOMED Search",
        description: "Search SNOMED CT clinical terminology",
        method: "GET",
        endpoint: "/api/v1/terminology/snomed",
        queryParams: {
          query: "diabetes",
          limit: 10,
        },
        body: null,
      },
      {
        id: "icd10-lookup",
        name: "ICD-10 Lookup",
        description: "Lookup ICD-10 diagnosis codes",
        method: "GET",
        endpoint: "/api/v1/terminology/icd10",
        queryParams: {
          code: "E11",
          description: true,
        },
        body: null,
      },
      {
        id: "loinc-mapping",
        name: "LOINC Mapping",
        description: "Map lab tests to LOINC codes",
        method: "POST",
        endpoint: "/api/v1/terminology/loinc/map",
        body: {
          test_name: "Hemoglobin A1c",
          system: "LOINC",
          include_properties: true,
        },
      },
    ],
  },
};

// Helper function to get the full URL with query parameters
export const buildEndpointUrl = (baseEndpoint, queryParams) => {
  if (!queryParams || Object.keys(queryParams).length === 0) {
    return baseEndpoint;
  }
  const queryString = new URLSearchParams(queryParams).toString();
  return `${baseEndpoint}?${queryString}`;
};
