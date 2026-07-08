export const articles = [
  {
    slug: "getting-started",
    title: "Getting started with MedTechTools",
    summary: "A quick guide to creating an API key, sending your first payload, and reading the response.",
    desc: "A quick guide to creating an API key, sending your first payload, and reading the response.",
    tags: ["Guide", "Setup"],
    content: `
      <p>MedTechTools is designed to make healthcare data workflows faster and less frustrating. The fastest way to begin is to request an API key and send a small sample payload.</p>
      <h2>1. Request your API key</h2>
      <p>Use the registration flow to create a free API key. The key is then used to authenticate your requests.</p>
      <h2>2. Send a sample request</h2>
      <p>Start with a simple patient payload and include a few observations or conditions. This gives you immediate feedback on validation and explanation output.</p>
      <h2>3. Review the response</h2>
      <p>MedTechTools will return validation issues, explanations, and any auto-fixes that were applied. You can then refine your payload or use the output as a starting point for integration work.</p>
    `,
  },
  {
    slug: "common-fhir-issues",
    title: "Common FHIR issues and how to fix them",
    summary: "Learn how the platform handles enum values, date formats, and field-name mismatches.",
    desc: "Learn how the platform handles enum values, date formats, and field-name mismatches.",
    tags: ["FHIR", "Troubleshooting"],
    content: `
      <p>Many FHIR integration issues come from small but costly formatting problems. These are usually easy to fix once you can see what the validator is flagging.</p>
      <h2>Common problems</h2>
      <ul>
        <li>Gender values like M or F instead of male or female</li>
        <li>Dates in local formats rather than ISO 8601</li>
        <li>Field names that do not match expected FHIR structure</li>
        <li>Missing or inconsistent terminology values</li>
      </ul>
      <h2>How MedTechTools helps</h2>
      <p>The platform explains each issue in plain English and applies known fixes so your data becomes valid faster.</p>
    `,
  },
  {
    slug: "api-first-validation",
    title: "Why healthcare teams use API-first validation",
    summary: "See how automation reduces manual cleanup and improves interoperability projects.",
    desc: "See how automation reduces manual cleanup and improves interoperability projects.",
    tags: ["Use cases", "Health tech"],
    content: `
      <p>API-first validation makes healthcare data quality checks easier to embed into real workflows. Instead of fixing everything manually at the end, teams can validate as data moves through their system.</p>
      <h2>Benefits</h2>
      <ul>
        <li>Less manual cleanup</li>
        <li>Faster onboarding for new integrations</li>
        <li>Better visibility into data quality issues</li>
        <li>Improved confidence before exchange or storage</li>
      </ul>
      <p>This approach is especially useful for startups and integration teams trying to ship quickly without sacrificing data quality.</p>
    `,
  },
  {
    slug: "streamlining-healthcare-data",
    title: "Streamlining Healthcare Data: An Introduction to MedTechTools",
    summary: "A practical overview of why MedTechTools exists and how it helps teams handle messy healthcare data more effectively.",
    desc: "A practical overview of why MedTechTools exists and how it helps teams handle messy healthcare data more effectively.",
    tags: ["Introduction", "FHIR", "Health tech"],
    content: `
      <p>In the world of healthcare technology, data interoperability is king. Fast Healthcare Interoperability Resources (FHIR) has quickly become the gold standard for exchanging electronic health records. However, any developer who has worked with FHIR knows that dealing with raw healthcare data can be a debugging nightmare. Inconsistent date formats, mismatched gender codes, and cryptic validation errors frequently stall integration workflows.</p>
      <p>Enter <strong>MedTechTools</strong>, a public beta utility specifically built for healthcare developers, integrators, and data teams to validate, explain, and correct FHIR data with a single API call.</p>
      <h2>The Core Challenge: Why FHIR Integration is Hard</h2>
      <p>Most health tech developers do not start with perfect FHIR data. They ingest legacy HL7 messages, custom JSON payloads, or unstructured spreadsheets. Turning this into FHIR-compliant resources often involves writing tedious custom mapping code, manually formatting strings, and sifting through dense schema errors.</p>
      <p>MedTechTools aims to replace this manual cleanup with an intelligent, automated pipeline.</p>
      <h2>Key Features of MedTechTools</h2>
      <h3>1. Smart Field Mapping</h3>
      <p>Instead of writing extensive boilerplate code to map incoming data fields to the FHIR standard, MedTechTools handles it automatically. Common aliases like DOB or Sex are recognized and routed to the correct FHIR fields.</p>
      <h3>2. Intelligent Auto-Fix Engine</h3>
      <p>If your payload contains minor formatting or convention errors, the platform does not just throw an error—it fixes them. This includes correcting gender values, date formatting, and status terms.</p>
      <h3>3. Human-Readable Error Explanations</h3>
      <p>When data issues are too complex for automatic fixes, MedTechTools uses a hybrid approach combining business rules and AI to return plain-English explanations instead of cryptic validation dumps.</p>
      <h3>4. Comprehensive Medical Code Lookups</h3>
      <p>The tool can validate terminology from LOINC, SNOMED CT, and RxNorm to support more accurate healthcare data exchange.</p>
      <h3>5. Patient-Centered Bundle Generation</h3>
      <p>Instead of forcing developers to stitch resources together manually, MedTechTools lets them send a single patient record and related resources in one request, generating a more complete bundle for EHR workflows.</p>
      <h2>Data Quality at a Glance: Scoring Grades</h2>
      <p>Every response includes a quality grade from A+ to D so teams can quickly assess the health of their data streams.</p>
      <h2>Getting Started</h2>
      <p>MedTechTools is currently in public beta and is designed to be easy to try. You can get up and running in under two minutes with simple curl or Python requests, and the launch tier includes a free plan with 500 API calls per month and no credit card required.</p>
      <p>If you are tired of spending hours debugging schema mismatches and want a cleaner, more reliable healthcare data workflow, you can explore the documentation and grab a free API key.</p>
    `,
  },
];

export const faqs = [
  {
    question: "Who is MedTechTools for?",
    answer: "It is built for healthcare developers, integration engineers, and startup teams working with FHIR payloads.",
  },
  {
    question: "Does it support auto-fixes?",
    answer: "Yes. The platform can explain and correct common issues like gender values, date formats, and invalid enums.",
  },
  {
    question: "Can I use it for patient bundles?",
    answer: "Yes. You can create patient-centered FHIR bundles that include related resources in one response.",
  },
];
