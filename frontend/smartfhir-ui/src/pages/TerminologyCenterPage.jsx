import { useState, useEffect, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";

const THEMES = {
  dark: {
    bg: "#0F1117",
    surface: "#1A1D27",
    border: "#2A2D3E",
    accent: "#4F8EF7",
    accentDim: "#1E3A6E",
    success: "#34D399",
    warning: "#FBBF24",
    error: "#F87171",
    muted: "#6B7280",
    text: "#E2E8F0",
    textDim: "#94A3B8",
    shadow: "rgba(0, 0, 0, 0.3)",
    shadowLight: "rgba(79, 142, 247, 0.1)",
  },
  light: {
    bg: "#F8FAFC",
    surface: "#FFFFFF",
    border: "#E2E8F0",
    accent: "#3B82F6",
    accentDim: "#DBEAFE",
    success: "#10B981",
    warning: "#F59E0B",
    error: "#EF4444",
    muted: "#64748B",
    text: "#1E293B",
    textDim: "#64748B",
    shadow: "rgba(0, 0, 0, 0.1)",
    shadowLight: "rgba(59, 130, 246, 0.1)",
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// MOCK DATA
// ═══════════════════════════════════════════════════════════════════════════════

const MOCK_TERMINOLOGY_DATA = {
  "44054006": {
    system: "SNOMED CT",
    code: "44054006",
    display: "Type 2 diabetes mellitus",
    description: "A disorder of carbohydrate metabolism characterized by high blood glucose levels caused by insulin resistance.",
    category: "Clinical finding",
    fhirSystem: "http://snomed.info/sct",
    parents: ["73211009 - Diabetes mellitus"],
    children: ["440383007 - Type 2 diabetes mellitus with hyperosmolarity"],
    related: ["250.00 - Diabetes mellitus without mention of complication"],
    synonyms: ["DM2", "Non-insulin-dependent diabetes"],
  },
  "E11": {
    system: "ICD-10",
    code: "E11",
    display: "Type 2 diabetes mellitus",
    description: "Type 2 diabetes with or without complications.",
    category: "Diagnosis",
    fhirSystem: "http://hl7.org/fhir/sid/icd-10",
    parents: ["E10-E14 - Diabetes mellitus"],
    children: ["E11.0 - With hyperosmolarity"],
    related: ["44054006 - SNOMED CT equivalent"],
    synonyms: ["NIDDM", "T2DM"],
  },
  "I10": {
    system: "ICD-10",
    code: "I10",
    display: "Essential (primary) hypertension",
    description: "High blood pressure not attributed to secondary causes.",
    category: "Diagnosis",
    fhirSystem: "http://hl7.org/fhir/sid/icd-10",
    parents: ["I10-I16 - Diseases of the circulatory system"],
    children: ["I11 - Hypertensive heart disease"],
    related: ["38341003 - SNOMED CT equivalent"],
    synonyms: ["Hypertension", "HTN", "Primary hypertension"],
  },
  "38341003": {
    system: "SNOMED CT",
    code: "38341003",
    display: "Hypertension",
    description: "Abnormally high systemic arterial blood pressure.",
    category: "Clinical finding",
    fhirSystem: "http://snomed.info/sct",
    parents: ["34065005 - Vasculitis"],
    children: ["59720008 - Hypertensive crisis"],
    related: ["I10 - ICD-10 equivalent"],
    synonyms: ["High blood pressure", "HTN", "Arterial hypertension"],
  },
  "J45": {
    system: "ICD-10",
    code: "J45",
    display: "Asthma",
    description: "Chronic inflammatory disorder of the airways.",
    category: "Diagnosis",
    fhirSystem: "http://hl7.org/fhir/sid/icd-10",
    parents: ["J40-J47 - Diseases of the respiratory system"],
    children: ["J45.9 - Asthma, unspecified"],
    related: ["195967001 - SNOMED CT equivalent"],
    synonyms: ["Asthmatic condition"],
  },
  "195967001": {
    system: "SNOMED CT",
    code: "195967001",
    display: "Asthma",
    description: "Chronic inflammatory airways disease with reversible airflow obstruction.",
    category: "Clinical finding",
    fhirSystem: "http://snomed.info/sct",
    parents: ["50043002 - Disorder of respiratory system"],
    children: ["426656000 - Severe persistent asthma"],
    related: ["J45 - ICD-10 equivalent"],
    synonyms: ["Bronchial asthma", "Reactive airway disease"],
  },
  "4548-4": {
    system: "LOINC",
    code: "4548-4",
    display: "Hemoglobin A1c/Hemoglobin.total in Blood",
    description: "Glycated hemoglobin as percentage of total hemoglobin.",
    category: "Laboratory Tests",
    fhirSystem: "http://loinc.org",
    parents: ["LP14559-6 - Hemoglobin"],
    children: [],
    related: ["LG7820-8 - LOINC reference range"],
    synonyms: ["HbA1c", "Glycated Hemoglobin", "Hemoglobin A1c"],
  },
  "2339-0": {
    system: "LOINC",
    code: "2339-0",
    display: "Glucose [Mass/volume] in Blood",
    description: "Glucose concentration in blood plasma.",
    category: "Laboratory Tests",
    fhirSystem: "http://loinc.org",
    parents: ["LP14559-6 - Glucose"],
    children: [],
    related: ["2345-9 - Glucose [Moles/volume] in Blood"],
    synonyms: ["Blood glucose", "Plasma glucose", "Serum glucose"],
  },
  "860975": {
    system: "RxNorm",
    code: "860975",
    display: "Metformin 500 MG Oral Tablet",
    description: "A biguanide oral antidiabetic medication commonly used for type 2 diabetes.",
    category: "Medications",
    fhirSystem: "http://www.nlm.nih.gov/research/umls/rxnorm",
    parents: ["4815 - Metformin"],
    children: ["1049630 - Metformin 500 MG and Sitagliptin 50 MG Oral Tablet"],
    related: ["25789 - Metformin"],
    synonyms: ["Glucophage", "Metformin HCl"],
  },
  "1049630": {
    system: "RxNorm",
    code: "1049630",
    display: "Aspirin 325 MG Oral Tablet",
    description: "Acetylsalicylic acid used for pain relief and blood clotting prevention.",
    category: "Medications",
    fhirSystem: "http://www.nlm.nih.gov/research/umls/rxnorm",
    parents: ["1191 - Aspirin"],
    children: [],
    related: ["4024 - Aspirin"],
    synonyms: ["Acetylsalicylic acid", "ASA", "Bayer Aspirin"],
  },
  "J18.9": { system: "ICD-10", code: "J18.9", display: "Pneumonia, unspecified organism", description: "Inflammation and infection of lung tissue without a specified organism.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Pneumonia", "Lung infection"] },
  "J44.9": { system: "ICD-10", code: "J44.9", display: "Chronic obstructive pulmonary disease, unspecified", description: "Chronic airflow limitation not otherwise specified.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["COPD", "Chronic obstructive lung disease"] },
  "I50.9": { system: "ICD-10", code: "I50.9", display: "Heart failure, unspecified", description: "Cardiac pump dysfunction without a specified type or acuity.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["CHF", "Congestive heart failure"] },
  "N18.9": { system: "ICD-10", code: "N18.9", display: "Chronic kidney disease, unspecified", description: "Long-term impairment of kidney function without a specified stage.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["CKD", "Chronic renal disease"] },
  "F32.9": { system: "ICD-10", code: "F32.9", display: "Major depressive disorder, single episode, unspecified", description: "Depressive episode without additional severity specification.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Depression", "Major depression"] },
  "F41.9": { system: "ICD-10", code: "F41.9", display: "Anxiety disorder, unspecified", description: "Clinically significant anxiety without a more specific disorder classification.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Anxiety", "Anxiety disorder"] },
  "G43.909": { system: "ICD-10", code: "G43.909", display: "Migraine, unspecified, not intractable, without status migrainosus", description: "Migraine headache without intractability or prolonged status migrainosus.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Migraine headache", "Migraine"] },
  "N39.0": { system: "ICD-10", code: "N39.0", display: "Urinary tract infection, site not specified", description: "Infection involving the urinary tract without a specified site.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["UTI", "Urinary tract infection"] },
  "M54.5": { system: "ICD-10", code: "M54.5", display: "Low back pain", description: "Pain localized to the lower back region.", category: "Diagnosis", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Lumbago", "Lower back pain"] },
  "29046": { system: "RxNorm", code: "29046", display: "Lisinopril", description: "ACE inhibitor used for hypertension and heart failure.", category: "Medications", fhirSystem: "http://www.nlm.nih.gov/research/umls/rxnorm", synonyms: ["Prinivil", "Zestril"] },
  "83367": { system: "RxNorm", code: "83367", display: "Atorvastatin", description: "Statin medication used to lower cholesterol.", category: "Medications", fhirSystem: "http://www.nlm.nih.gov/research/umls/rxnorm", synonyms: ["Lipitor"] },
  "435": { system: "RxNorm", code: "435", display: "Albuterol", description: "Short-acting beta agonist used for bronchospasm relief.", category: "Medications", fhirSystem: "http://www.nlm.nih.gov/research/umls/rxnorm", synonyms: ["Salbutamol", "Ventolin"] },
  "161": { system: "RxNorm", code: "161", display: "Acetaminophen", description: "Analgesic and antipyretic used for pain and fever.", category: "Medications", fhirSystem: "http://www.nlm.nih.gov/research/umls/rxnorm", synonyms: ["Paracetamol", "Tylenol"] },
  "718-7": { system: "LOINC", code: "718-7", display: "Hemoglobin [Mass/volume] in Blood", description: "Hemoglobin concentration measured in whole blood.", category: "Laboratory Tests", fhirSystem: "http://loinc.org", synonyms: ["Hgb", "Hemoglobin"] },
  "2093-3": { system: "LOINC", code: "2093-3", display: "Cholesterol [Mass/volume] in Serum or Plasma", description: "Total cholesterol concentration in serum or plasma.", category: "Laboratory Tests", fhirSystem: "http://loinc.org", synonyms: ["Total cholesterol", "Cholesterol"] },
  "2160-0": { system: "LOINC", code: "2160-0", display: "Creatinine [Mass/volume] in Serum or Plasma", description: "Serum or plasma creatinine for kidney function assessment.", category: "Laboratory Tests", fhirSystem: "http://loinc.org", synonyms: ["Serum creatinine", "Creatinine"] },
  "6690-2": { system: "LOINC", code: "6690-2", display: "Leukocytes [#/volume] in Blood by Automated count", description: "White blood cell count measured from blood.", category: "Laboratory Tests", fhirSystem: "http://loinc.org", synonyms: ["WBC", "White blood cell count"] },
  "80146002": { system: "SNOMED CT", code: "80146002", display: "Appendectomy", description: "Surgical removal of the appendix.", category: "Procedures", fhirSystem: "http://snomed.info/sct", synonyms: ["Appendix removal"] },
  "387713003": { system: "SNOMED CT", code: "387713003", display: "Surgical procedure", description: "General class for operative or invasive surgical interventions.", category: "Procedures", fhirSystem: "http://snomed.info/sct", synonyms: ["Surgery", "Operation"] },
  "73761001": { system: "SNOMED CT", code: "73761001", display: "Colonoscopy", description: "Endoscopic examination of the colon.", category: "Procedures", fhirSystem: "http://snomed.info/sct", synonyms: ["Lower GI endoscopy"] },
  "710830005": { system: "SNOMED CT", code: "710830005", display: "Administration of vaccine", description: "Procedure for giving an immunization product.", category: "Procedures", fhirSystem: "http://snomed.info/sct", synonyms: ["Vaccination", "Immunization administration"] },
  "225358003": { system: "SNOMED CT", code: "225358003", display: "Wound care", description: "Care activity for assessment and management of a wound.", category: "Procedures", fhirSystem: "http://snomed.info/sct", synonyms: ["Dressing change", "Wound management"] },
  "168537006": { system: "SNOMED CT", code: "168537006", display: "Chest X-ray", description: "Plain radiographic imaging examination of the chest.", category: "Imaging/Radiology", fhirSystem: "http://snomed.info/sct", synonyms: ["CXR", "Chest radiograph"] },
  "241615005": { system: "SNOMED CT", code: "241615005", display: "Computed tomography of head", description: "CT imaging study of the head.", category: "Imaging/Radiology", fhirSystem: "http://snomed.info/sct", synonyms: ["Head CT", "CT brain"] },
  "113091000": { system: "SNOMED CT", code: "113091000", display: "Magnetic resonance imaging", description: "Imaging procedure using magnetic fields and radiofrequency pulses.", category: "Imaging/Radiology", fhirSystem: "http://snomed.info/sct", synonyms: ["MRI", "MR imaging"] },
  "16310003": { system: "SNOMED CT", code: "16310003", display: "Ultrasonography", description: "Diagnostic imaging using high-frequency sound waves.", category: "Imaging/Radiology", fhirSystem: "http://snomed.info/sct", synonyms: ["Ultrasound", "Sonography"] },
  "45036003": { system: "SNOMED CT", code: "45036003", display: "Mammography", description: "Radiographic imaging of breast tissue.", category: "Imaging/Radiology", fhirSystem: "http://snomed.info/sct", synonyms: ["Mammogram"] },
  "R50.9": { system: "ICD-10", code: "R50.9", display: "Fever, unspecified", description: "Elevated body temperature without a specified cause.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Pyrexia", "Fever"] },
  "R05": { system: "ICD-10", code: "R05", display: "Cough", description: "Symptom of forceful expiratory effort against a closed glottis.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Coughing"] },
  "R51": { system: "ICD-10", code: "R51", display: "Headache", description: "Pain or discomfort in the head region.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Cephalgia", "Head pain"] },
  "R07.9": { system: "ICD-10", code: "R07.9", display: "Chest pain, unspecified", description: "Pain in the chest without specified cause or character.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Chest discomfort"] },
  "R06.02": { system: "ICD-10", code: "R06.02", display: "Shortness of breath", description: "Subjective difficulty breathing or sensation of breathlessness.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Dyspnea", "Breathlessness"] },
  "R53.83": { system: "ICD-10", code: "R53.83", display: "Other fatigue", description: "Tiredness, lack of energy, or exhaustion not otherwise specified.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Fatigue", "Tiredness"] },
  "R11.0": { system: "ICD-10", code: "R11.0", display: "Nausea", description: "Unpleasant sensation associated with the urge to vomit.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Queasiness"] },
  "R10.9": { system: "ICD-10", code: "R10.9", display: "Unspecified abdominal pain", description: "Pain localized to the abdomen without further specification.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Abdominal pain", "Belly pain"] },
  "R42": { system: "ICD-10", code: "R42", display: "Dizziness and giddiness", description: "Sensation of imbalance, lightheadedness, or spinning.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Lightheadedness", "Vertigo"] },
  "R21": { system: "ICD-10", code: "R21", display: "Rash and other nonspecific skin eruption", description: "Nonspecific visible change or eruption on the skin.", category: "Symptoms", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["Skin rash", "Eruption"] },
  "50043002": { system: "SNOMED CT", code: "50043002", display: "Disorder of respiratory system", description: "Disease or functional abnormality involving the respiratory tract.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Respiratory disorder"] },
  "49601007": { system: "SNOMED CT", code: "49601007", display: "Disorder of cardiovascular system", description: "Disease or functional abnormality involving the heart or blood vessels.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Cardiovascular disorder"] },
  "118940003": { system: "SNOMED CT", code: "118940003", display: "Disorder of nervous system", description: "Disease or functional abnormality involving the central or peripheral nervous system.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Neurologic disorder"] },
  "53619000": { system: "SNOMED CT", code: "53619000", display: "Disorder of digestive system", description: "Disease or functional abnormality involving the gastrointestinal tract.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Gastrointestinal disorder", "GI disorder"] },
  "128121009": { system: "SNOMED CT", code: "128121009", display: "Disorder of musculoskeletal system", description: "Disease or functional abnormality involving bones, joints, muscles, or connective tissue.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Musculoskeletal disorder"] },
  "90708001": { system: "SNOMED CT", code: "90708001", display: "Kidney disease", description: "Disease or functional abnormality involving the kidneys.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Renal disease"] },
  "363346000": { system: "SNOMED CT", code: "363346000", display: "Malignant neoplastic disease", description: "Body-system-spanning malignant tumor disorder grouping.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Cancer", "Malignancy"] },
  "414916001": { system: "SNOMED CT", code: "414916001", display: "Obesity", description: "Nutritional and metabolic disorder characterized by excess adiposity.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Obese", "Excess body weight"] },
  "123037004": { system: "SNOMED CT", code: "123037004", display: "Body structure", description: "SNOMED CT hierarchy for anatomical body structures.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Anatomical structure", "Body site"] },
  "404684003": { system: "SNOMED CT", code: "404684003", display: "Clinical finding", description: "SNOMED CT hierarchy for observations, symptoms, and diagnoses.", category: "Body Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["Finding", "Clinical observation"] },
  "condition-code": { system: "FHIR ValueSet", code: "VS-CONDITION", display: "Condition/Problem/Diagnosis Codes", description: "FHIR value set used for Condition.code concepts.", category: "FHIR ValueSets", fhirSystem: "http://hl7.org/fhir/ValueSet/condition-code", synonyms: ["condition-code", "Condition codes", "Diagnosis value set"] },
  "observation-codes": { system: "FHIR ValueSet", code: "VS-OBSERVATION", display: "LOINC Codes", description: "FHIR value set commonly used for Observation.code concepts.", category: "FHIR ValueSets", fhirSystem: "http://hl7.org/fhir/ValueSet/observation-codes", synonyms: ["observation-codes", "Observation codes", "LOINC value set"] },
  "medication-codes": { system: "FHIR ValueSet", code: "VS-MEDICATION", display: "Medication Codes", description: "FHIR value set for coded medication concepts.", category: "FHIR ValueSets", fhirSystem: "http://hl7.org/fhir/ValueSet/medication-codes", synonyms: ["medication-codes", "Medication value set", "Drug codes"] },
  "procedure-code": { system: "FHIR ValueSet", code: "VS-PROCEDURE", display: "Procedure Codes", description: "FHIR value set used for Procedure.code concepts.", category: "FHIR ValueSets", fhirSystem: "http://hl7.org/fhir/ValueSet/procedure-code", synonyms: ["procedure-code", "Procedure value set"] },
  "body-site": { system: "FHIR ValueSet", code: "VS-BODY-SITE", display: "SNOMED CT Body Structures", description: "FHIR value set for body site and anatomical location concepts.", category: "FHIR ValueSets", fhirSystem: "http://hl7.org/fhir/ValueSet/body-site", synonyms: ["body-site", "Body site value set", "Anatomy codes"] },
  "snomed-system": { system: "Code System", code: "CS-SNOMED-CT", display: "SNOMED CT", description: "Comprehensive clinical terminology for findings, procedures, body structures, and other healthcare concepts.", category: "Code Systems", fhirSystem: "http://snomed.info/sct", synonyms: ["http://snomed.info/sct", "Systematized Nomenclature of Medicine Clinical Terms"] },
  "icd10-system": { system: "Code System", code: "CS-ICD-10", display: "ICD-10", description: "International classification used for diagnosis and morbidity coding.", category: "Code Systems", fhirSystem: "http://hl7.org/fhir/sid/icd-10", synonyms: ["http://hl7.org/fhir/sid/icd-10", "ICD-10-CM", "International Classification of Diseases"] },
  "loinc-system": { system: "Code System", code: "CS-LOINC", display: "LOINC", description: "Terminology for laboratory tests, clinical measurements, surveys, and observations.", category: "Code Systems", fhirSystem: "http://loinc.org", synonyms: ["http://loinc.org", "Logical Observation Identifiers Names and Codes"] },
  "rxnorm-system": { system: "Code System", code: "CS-RXNORM", display: "RxNorm", description: "Normalized naming system for medications and clinical drugs.", category: "Code Systems", fhirSystem: "http://www.nlm.nih.gov/research/umls/rxnorm", synonyms: ["http://www.nlm.nih.gov/research/umls/rxnorm", "RxNorm drug terminology"] },
  "ucum-system": { system: "Code System", code: "CS-UCUM", display: "UCUM", description: "Unified Code for Units of Measure used for coded units in observations and medication dosing.", category: "Code Systems", fhirSystem: "http://unitsofmeasure.org", synonyms: ["http://unitsofmeasure.org", "Units of measure", "UCUM units"] },
};

const ALL_RESULTS = Object.entries(MOCK_TERMINOLOGY_DATA).map(([code, data]) => ({
  code,
  ...data,
}));

const AI_FINDER_STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "by",
  "daily",
  "for",
  "from",
  "has",
  "have",
  "in",
  "is",
  "mg",
  "of",
  "on",
  "or",
  "patient",
  "reports",
  "taking",
  "the",
  "to",
  "with",
]);

const AI_EXAMPLE_PROMPTS = [
  "Patient has type 2 diabetes and hypertension, taking metformin 500mg daily",
  "Shortness of breath with cough and chest x-ray ordered",
  "Chronic kidney disease with creatinine lab and lisinopril",
];

function normalizeFinderText(value = "") {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9.\- ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function getFinderTokens(value) {
  return normalizeFinderText(value)
    .split(" ")
    .filter((token) => token.length > 1 && !AI_FINDER_STOP_WORDS.has(token));
}

function scoreTerminologyResult(result, promptTokens, normalizedPrompt) {
  const synonyms = result.synonyms || [];
  const searchableParts = [
    result.code,
    result.display,
    result.description,
    result.category,
    result.system,
    ...synonyms,
  ];
  const searchableText = normalizeFinderText(searchableParts.join(" "));
  const displayText = normalizeFinderText(result.display);
  const synonymText = normalizeFinderText(synonyms.join(" "));
  const descriptionText = normalizeFinderText(result.description);

  let score = 0;
  const reasons = [];

  if (normalizedPrompt.includes(displayText) && displayText) {
    score += 45;
    reasons.push("Direct concept match");
  }

  if (normalizedPrompt.includes(normalizeFinderText(result.code))) {
    score += 35;
    reasons.push("Code mentioned");
  }

  synonyms.forEach((synonym) => {
    const normalizedSynonym = normalizeFinderText(synonym);
    if (normalizedSynonym && normalizedPrompt.includes(normalizedSynonym)) {
      score += 28;
      reasons.push(`Matched synonym: ${synonym}`);
    }
  });

  promptTokens.forEach((token) => {
    if (displayText.includes(token)) score += 10;
    if (synonymText.includes(token)) score += 8;
    if (descriptionText.includes(token)) score += 4;
    if (searchableText.includes(token)) score += 2;
  });

  const categoryHints = [
    { terms: ["lab", "labs", "test", "blood", "glucose", "a1c", "creatinine"], category: "Laboratory Tests", bonus: 10 },
    { terms: ["med", "medication", "drug", "tablet", "dose"], category: "Medications", bonus: 10 },
    { terms: ["diagnosis", "condition", "disease"], category: "Diagnosis", bonus: 8 },
    { terms: ["procedure", "surgery", "xray", "x-ray", "ct", "mri", "ultrasound"], category: "Procedures", bonus: 8 },
    { terms: ["symptom", "pain", "cough", "fever", "nausea", "dizziness"], category: "Symptoms", bonus: 8 },
  ];

  categoryHints.forEach((hint) => {
    const hasHint = hint.terms.some((term) => normalizedPrompt.includes(term));
    if (hasHint && result.category === hint.category) {
      score += hint.bonus;
      reasons.push(`${hint.category} context`);
    }
  });

  return {
    ...result,
    confidence: Math.min(99, Math.round(score)),
    matchReason: reasons.slice(0, 3),
    score,
  };
}

function findTerminologyCodes(prompt) {
  const normalizedPrompt = normalizeFinderText(prompt);
  const promptTokens = getFinderTokens(prompt);

  if (!normalizedPrompt || promptTokens.length === 0) {
    return [];
  }

  return ALL_RESULTS.map((result) =>
    scoreTerminologyResult(result, promptTokens, normalizedPrompt)
  )
    .filter((result) => result.score >= 12)
    .sort((a, b) => b.score - a.score || a.display.localeCompare(b.display))
    .slice(0, 8)
    .map((result) => ({
      ...result,
      matchReason:
        result.matchReason.length > 0
          ? result.matchReason
          : ["Related wording found in terminology record"],
    }));
}

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITY COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

function FilterChip({ label, active, onClick, colors, count, variant = "default" }) {
  const isSystemRow = variant === "system";
  return (
    <button
      onClick={onClick}
      style={{
        padding: "8px 14px",
        borderRadius: 20,
        border: active 
          ? `1px solid ${isSystemRow ? colors.accent : colors.border}` 
          : `1px solid ${isSystemRow ? colors.accent + "66" : colors.border}`,
        background: active
          ? isSystemRow 
            ? `linear-gradient(135deg, ${colors.accent}22, ${colors.accent}11)`
            : colors.bg
          : isSystemRow 
            ? colors.accent + "15"
            : colors.surface,
        color: active ? colors.accent : colors.text,
        cursor: "pointer",
        fontWeight: active ? 700 : 500,
        fontSize: 13,
        transition: "all 0.2s ease",
        whiteSpace: "nowrap",
        display: "flex",
        alignItems: "center",
        gap: 6,
      }}
    >
      {label}
      {count !== undefined && (
        <span style={{
          background: active ? (isSystemRow ? colors.accent + "33" : colors.bg) : colors.bg,
          color: active ? colors.accent : colors.textDim,
          padding: "2px 6px",
          borderRadius: 10,
          fontSize: 11,
          fontWeight: 600,
        }}>
          {count}
        </span>
      )}
    </button>
  );
}

function getSystemStatus(system) {
  // Mock status logic based on system type
  const statusMap = {
    "SNOMED CT": { status: "Active", version: "v4.0.1", color: "#34D399" },
    "ICD-10": { status: "Active", version: "v2023", color: "#34D399" },
    "LOINC": { status: "Active", version: "v2.74", color: "#34D399" },
    "RxNorm": { status: "Active", version: "v5.0.1", color: "#34D399" },
    "FHIR ValueSet": { status: "Active", version: "R4", color: "#34D399" },
    "Code System": { status: "Active", version: "R4", color: "#34D399" },
  };
  return statusMap[system] || { status: "Active", version: "", color: "#34D399" };
}

function TerminologyCard({ result, colors, onSelect, onCopy, favorites, onToggleFavorite }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const isLongDescription = result.description && result.description.length > 120;
  const systemStatus = getSystemStatus(result.system);
  
  return (
    <div
      data-terminology-card="true"
      onClick={() => onSelect(result)}
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
        padding: 18,
        cursor: "pointer",
        transition: "all 0.3s ease",
        boxShadow: `0 2px 8px ${colors.shadow}`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        gap: 12,
        position: "relative",
        minHeight: 240,
      }}
      onMouseEnter={(e) => {
        setIsHovered(true);
        e.currentTarget.style.borderColor = colors.accent;
        e.currentTarget.style.boxShadow = `0 4px 16px ${colors.shadowLight}`;
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        setIsHovered(false);
        e.currentTarget.style.borderColor = colors.border;
        e.currentTarget.style.boxShadow = `0 2px 8px ${colors.shadow}`;
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      {/* Top row: System badge, Code with copy button, and Category badge */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8, marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
          {/* Identifiers Group: Code first, then System Badge */}
          <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
            <div
              style={{
                color: "#FFFFFF",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                fontSize: 15,
                fontWeight: 800,
                letterSpacing: "0.5px",
              }}
            >
              {result.code}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCopy("code", result.code);
              }}
              style={{
                background: "transparent",
                border: "none",
                color: colors.muted,
                cursor: "pointer",
                padding: "2px 4px",
                fontSize: 12,
                transition: "color 0.2s ease",
                display: "inline-flex",
                alignItems: "center",
                verticalAlign: "middle",
              }}
              title="Copy code"
              onMouseEnter={(e) => (e.currentTarget.style.color = colors.text)}
              onMouseLeave={(e) => (e.currentTarget.style.color = colors.muted)}
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
          </div>

          <div
            style={{
              background: colors.accentDim,
              color: colors.accent,
              padding: "3px 8px",
              borderRadius: 6,
              fontSize: 10,
              fontWeight: 700,
              whiteSpace: "nowrap",
            }}
          >
            {result.system}
          </div>

          {systemStatus.version && (
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                background: systemStatus.color + "22",
                color: systemStatus.color,
                padding: "3px 8px",
                borderRadius: 6,
                fontSize: 10,
                fontWeight: 700,
                alignSelf: "center",
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: systemStatus.color }} />
              <span>{systemStatus.version}</span>
            </div>
          )}
        </div>

        {/* Category badge styled as a background-tinted border badge */}
        <span
          style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: `1px solid ${colors.border}`,
            color: colors.textDim,
            padding: "3px 8px",
            borderRadius: 6,
            fontSize: 10,
            fontWeight: 700,
            whiteSpace: "nowrap",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          {result.category}
        </span>
      </div>

      {/* Concept Name - Primary Heading */}
      <div style={{ color: "#FFFFFF", fontSize: 17, fontWeight: 800, lineHeight: 1.3 }}>
        {result.display}
      </div>

      {/* Description with truncation */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            color: "rgba(255, 255, 255, 0.6)",
            fontSize: 13,
            lineHeight: 1.5,
            display: isExpanded ? "block" : "-webkit-box",
            WebkitLineClamp: isExpanded ? "unset" : 2,
            WebkitBoxOrient: "vertical",
            overflow: isExpanded ? "visible" : "hidden",
          }}
        >
          {result.description}
        </div>
        {isLongDescription && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            style={{
              background: "none",
              border: "none",
              color: colors.accent,
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              padding: 0,
              marginTop: 4,
            }}
          >
            {isExpanded ? "Show less" : "..."}
          </button>
        )}
      </div>

      {/* Bottom row: Match indicator and FHIR button */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {typeof result.confidence === "number" && (
            <span
              style={{
                background: colors.success + "22",
                color: colors.success,
                padding: "4px 10px",
                borderRadius: 6,
                fontSize: 11,
                fontWeight: 700,
              }}
            >
              {result.confidence}% match
            </span>
          )}
          {result.matchReason?.slice(0, 1).map((reason) => (
            <span
              key={reason}
              style={{
                background: colors.bg,
                color: colors.textDim,
                border: `1px solid ${colors.border}`,
                padding: "4px 10px",
                borderRadius: 6,
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              {reason}
            </span>
          ))}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onCopy(
              "fhir",
              JSON.stringify(
                {
                  coding: [
                    {
                      system: result.fhirSystem,
                      code: result.code,
                      display: result.display,
                    },
                  ],
                },
                null,
                2
              )
            );
          }}
          style={{
            background: colors.accent + "15",
            border: `1px solid ${colors.accent}`,
            color: colors.accent,
            borderRadius: 6,
            padding: "6px 12px",
            cursor: "pointer",
            fontSize: 12,
            fontWeight: 600,
            transition: "all 0.2s ease",
            whiteSpace: "nowrap",
          }}
        >
          ⚡ Generate FHIR
        </button>
      </div>

      {/* View Raw JSON link - appears on hover */}
      {isHovered && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onCopy(
              "fhir",
              JSON.stringify(
                {
                  coding: [
                    {
                      system: result.fhirSystem,
                      code: result.code,
                      display: result.display,
                    },
                  ],
                },
                null,
                2
              )
            );
          }}
          style={{
            position: "absolute",
            bottom: 8,
            right: 8,
            background: "none",
            border: "none",
            color: colors.textDim,
            fontSize: 11,
            fontWeight: 500,
            cursor: "pointer",
            padding: 0,
            zIndex: 10,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = colors.accent)}
          onMouseLeave={(e) => (e.currentTarget.style.color = colors.textDim)}
        >
          View Raw JSON →
        </button>
      )}
    </div>
  );

}

function DetailPanel({ selected, colors, onCopy, onClose, panelRef }) {
  if (!selected) return null;

  const fhirCoding = JSON.stringify({
    coding: [{
      system: selected.fhirSystem,
      code: selected.code,
      display: selected.display,
    }],
  }, null, 2);

  return (
    <div
      ref={panelRef}
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
        padding: 20,
        display: "flex",
        flexDirection: "column",
        gap: 16,
        maxHeight: "100vh",
        overflowY: "auto",
        boxShadow: `0 2px 12px ${colors.shadow}`,
      }}
    >
      {/* Header */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 12 }}>
          <div>
            <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
              Code Details
            </div>
            <div style={{ color: colors.text, fontSize: 18, fontWeight: 700 }}>
              {selected.display}
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close code details"
            title="Close"
            style={{
              background: colors.bg,
              border: `1px solid ${colors.border}`,
              color: colors.text,
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 16,
              fontWeight: 700,
              lineHeight: 1,
              minWidth: 32,
              height: 32,
            }}
          >
            x
          </button>
        </div>
      </div>

      {/* Full Description */}
      <div>
        <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
          Description
        </div>
        <div style={{ color: colors.textDim, fontSize: 13, lineHeight: 1.6 }}>
          {selected.description}
        </div>
      </div>

      {/* System URL */}
      <div>
        <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
          FHIR System
        </div>
        <code
          style={{
            background: colors.bg,
            border: `1px solid ${colors.border}`,
            borderRadius: 6,
            padding: 10,
            display: "block",
            fontSize: 12,
            color: colors.accent,
            fontFamily: "monospace",
            wordBreak: "break-all",
            cursor: "pointer",
          }}
          onClick={() => onCopy("system", selected.fhirSystem)}
          title="Click to copy"
        >
          {selected.fhirSystem}
        </code>
      </div>

      {/* Parents */}
      {selected.parents && selected.parents.length > 0 && (
        <div>
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
            Parents
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {selected.parents.map((parent, i) => (
              <div
                key={i}
                style={{
                  background: colors.bg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 6,
                  padding: 10,
                  fontSize: 12,
                  color: colors.textDim,
                }}
              >
                {parent}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Synonyms */}
      {selected.synonyms && selected.synonyms.length > 0 && (
        <div>
          <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
            Synonyms
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {selected.synonyms.map((syn, i) => (
              <span
                key={i}
                style={{
                  background: colors.accent + "22",
                  color: colors.accent,
                  padding: "4px 10px",
                  borderRadius: 12,
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                {syn}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* FHIR Coding */}
      <div>
        <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
          FHIR Coding
        </div>
        <pre
          style={{
            background: colors.bg,
            border: `1px solid ${colors.border}`,
            borderRadius: 6,
            padding: 12,
            fontSize: 11,
            color: colors.accent,
            fontFamily: "monospace",
            overflow: "auto",
            maxHeight: 200,
            cursor: "pointer",
            margin: 0,
          }}
          onClick={() => onCopy("fhir", fhirCoding)}
          title="Click to copy"
        >
          {fhirCoding}
        </pre>
        <button
          onClick={() => onCopy("fhir", fhirCoding)}
          style={{
            width: "100%",
            marginTop: 8,
            background: colors.accent,
            color: "#fff",
            border: "none",
            borderRadius: 6,
            padding: "8px 12px",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: 13,
            transition: "all 0.2s ease",
          }}
        >
          Copy JSON
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════

const CLINICAL_SAMPLE_TEXT = `Patient is a 58-year-old male with Type 2 Diabetes and Hypertension.

Currently taking Metformin 500 mg twice daily and Losartan 50 mg daily.

HbA1c is 8.2%.

Blood Pressure is 150/95.

Complains of occasional chest pain.`;

const CLINICAL_SAMPLE_INPUTS = [
  "Patient has Type 2 Diabetes and Hypertension.",
  "Patient complains of chest pain with elevated troponin.",
  "Patient taking Aspirin and Metformin.",
  "HbA1c is 8.1%.",
];

const MOCK_CLINICAL_CONCEPTS = [
  {
    id: "type-2-diabetes",
    section: "diagnoses",
    label: "Type 2 Diabetes",
    terms: ["type 2 diabetes", "t2dm", "dm2", "diabetes"],
    confidence: 99,
    reason: "The clinical note explicitly mentions Type 2 Diabetes.",
    relatedCodes: ["E11", "E11.9", "E11.65", "E10"],
    resourceType: "Condition",
    codes: [
      { systemName: "ICD-10", system: "http://hl7.org/fhir/sid/icd-10", code: "E11", display: "Type 2 diabetes mellitus" },
      { systemName: "SNOMED CT", system: "http://snomed.info/sct", code: "44054006", display: "Type 2 diabetes mellitus" },
    ],
  },
  {
    id: "hypertension",
    section: "diagnoses",
    label: "Hypertension",
    terms: ["hypertension", "high blood pressure", "blood pressure", "150/95"],
    confidence: 97,
    reason: "The note mentions Hypertension and includes an elevated blood pressure reading.",
    relatedCodes: ["I10", "I11", "38341003"],
    resourceType: "Condition",
    codes: [
      { systemName: "ICD-10", system: "http://hl7.org/fhir/sid/icd-10", code: "I10", display: "Essential (primary) hypertension" },
      { systemName: "SNOMED CT", system: "http://snomed.info/sct", code: "38341003", display: "Hypertension" },
    ],
  },
  {
    id: "chest-pain",
    section: "symptoms",
    label: "Chest pain",
    terms: ["chest pain", "chest discomfort"],
    confidence: 95,
    reason: "The clinical text states that the patient complains of occasional chest pain.",
    relatedCodes: ["R07.9", "29857009", "R07.89"],
    resourceType: "Condition",
    codes: [
      { systemName: "ICD-10", system: "http://hl7.org/fhir/sid/icd-10", code: "R07.9", display: "Chest pain, unspecified" },
      { systemName: "SNOMED CT", system: "http://snomed.info/sct", code: "29857009", display: "Chest pain" },
    ],
  },
  {
    id: "metformin",
    section: "medications",
    label: "Metformin",
    genericName: "Metformin",
    brandName: "Glucophage",
    terms: ["metformin", "glucophage"],
    confidence: 98,
    reason: "Metformin is listed as an active medication in the note.",
    relatedCodes: ["860975", "25789", "1049630"],
    resourceType: "MedicationRequest",
    codes: [
      { systemName: "RxNorm", system: "http://www.nlm.nih.gov/research/umls/rxnorm", code: "860975", display: "Metformin 500 MG Oral Tablet" },
    ],
  },
  {
    id: "losartan",
    section: "medications",
    label: "Losartan",
    genericName: "Losartan",
    brandName: "Cozaar",
    terms: ["losartan", "cozaar"],
    confidence: 96,
    reason: "Losartan 50 mg daily is listed as a current medication.",
    relatedCodes: ["52175", "979467", "Cozaar"],
    resourceType: "MedicationRequest",
    codes: [
      { systemName: "RxNorm", system: "http://www.nlm.nih.gov/research/umls/rxnorm", code: "52175", display: "Losartan" },
    ],
  },
  {
    id: "aspirin",
    section: "medications",
    label: "Aspirin",
    genericName: "Aspirin",
    brandName: "Bayer Aspirin",
    terms: ["aspirin", "asa", "bayer"],
    confidence: 96,
    reason: "Aspirin appears in the medication text.",
    relatedCodes: ["1049630", "1191", "4024"],
    resourceType: "MedicationRequest",
    codes: [
      { systemName: "RxNorm", system: "http://www.nlm.nih.gov/research/umls/rxnorm", code: "1049630", display: "Aspirin 325 MG Oral Tablet" },
    ],
  },
  {
    id: "hba1c",
    section: "labs",
    label: "HbA1c",
    units: "%",
    terms: ["hba1c", "a1c", "hemoglobin a1c"],
    confidence: 98,
    reason: "HbA1c is explicitly documented with a numeric result.",
    relatedCodes: ["4548-4", "17856-6"],
    resourceType: "Observation",
    codes: [
      { systemName: "LOINC", system: "http://loinc.org", code: "4548-4", display: "Hemoglobin A1c/Hemoglobin.total in Blood" },
    ],
  },
  {
    id: "blood-pressure",
    section: "vitals",
    label: "Blood Pressure",
    units: "mmHg",
    terms: ["blood pressure", "bp", "150/95"],
    confidence: 94,
    reason: "The note contains a blood pressure value of 150/95.",
    relatedCodes: ["85354-9", "8480-6", "8462-4"],
    resourceType: "Observation",
    codes: [
      { systemName: "LOINC", system: "http://loinc.org", code: "85354-9", display: "Blood pressure panel with all children optional" },
    ],
  },
  {
    id: "troponin",
    section: "labs",
    label: "Troponin",
    units: "ng/L",
    terms: ["troponin", "elevated troponin"],
    confidence: 93,
    reason: "The note mentions elevated troponin, which maps to a cardiac lab observation.",
    relatedCodes: ["89579-7", "10839-9"],
    resourceType: "Observation",
    codes: [
      { systemName: "LOINC", system: "http://loinc.org", code: "89579-7", display: "Troponin I.cardiac [Mass/volume] in Serum or Plasma by High sensitivity method" },
    ],
  },
  {
    id: "chest-xray",
    section: "procedures",
    label: "Chest X-ray",
    terms: ["chest x-ray", "chest xray", "cxr", "chest radiograph"],
    confidence: 92,
    reason: "The clinical note references a chest imaging procedure.",
    relatedCodes: ["168537006", "71020"],
    resourceType: "Procedure",
    codes: [
      { systemName: "SNOMED CT", system: "http://snomed.info/sct", code: "168537006", display: "Chest X-ray" },
      { systemName: "CPT", system: "http://www.ama-assn.org/go/cpt", code: "71020", display: "Radiologic examination, chest, 2 views" },
    ],
  },
];

const CLINICAL_SECTIONS = [
  { id: "diagnoses", title: "Detected Diagnoses", columns: ["ICD-10", "SNOMED CT"] },
  { id: "symptoms", title: "Detected Symptoms", columns: ["ICD-10", "SNOMED CT"] },
  { id: "medications", title: "Detected Medications", columns: ["RxNorm", "Generic Name", "Brand Name"] },
  { id: "labs", title: "Detected Laboratory Tests", columns: ["LOINC", "Display", "Reference Units"] },
  { id: "procedures", title: "Detected Procedures", columns: ["SNOMED", "CPT"] },
  { id: "vitals", title: "Detected Vital Signs", columns: ["LOINC", "Display", "Reference Units"] },
];

function detectClinicalConcepts(text) {
  const normalized = normalizeFinderText(text);
  if (!normalized) return [];
  return MOCK_CLINICAL_CONCEPTS.filter((concept) =>
    concept.terms.some((term) => normalized.includes(normalizeFinderText(term)))
  );
}

function codeCandidatesForText(text, preferredCategory) {
  return findTerminologyCodes(text)
    .filter((candidate) => !preferredCategory || candidate.category === preferredCategory || candidate.system !== "Code System")
    .slice(0, 2)
    .map((candidate) => ({
      systemName: candidate.system,
      system: candidate.fhirSystem,
      code: candidate.code,
      display: candidate.display,
    }));
}

function fallbackCodeForConcept(label, category) {
  if (category === "MEDICATION") {
    return [{ systemName: "RxNorm", system: "http://www.nlm.nih.gov/research/umls/rxnorm", code: "unmapped", display: label }];
  }
  if (category === "OBSERVATION") {
    return [{ systemName: "LOINC", system: "http://loinc.org", code: "unmapped", display: label }];
  }
  return [{ systemName: "Clinical Text", system: "urn:medspacy:extracted-text", code: "unmapped", display: label }];
}

function conceptsFromBackendAnalysis(analysis) {
  const concepts = [];

  (analysis.active_problems || []).forEach((problem, index) => {
    const category = problem.category === "SYMPTOM" ? "symptoms" : "diagnoses";
    const codes = codeCandidatesForText(problem.text, category === "symptoms" ? "Symptoms" : "Diagnosis");
    concepts.push({
      id: `medspacy-problem-${index}-${normalizeFinderText(problem.text).replace(/\s+/g, "-")}`,
      section: category,
      label: problem.text,
      confidence: 91,
      reason: `medSpaCy extracted "${problem.text}" as a current ${problem.category || "clinical concept"} after context filtering.`,
      relatedCodes: codes.map((code) => code.code),
      resourceType: "Condition",
      codes: codes.length > 0 ? codes : fallbackCodeForConcept(problem.text, problem.category),
    });
  });

  (analysis.active_medications || []).forEach((medication, index) => {
    const codes = codeCandidatesForText(medication.text, "Medications");
    concepts.push({
      id: `medspacy-med-${index}-${normalizeFinderText(medication.text).replace(/\s+/g, "-")}`,
      section: "medications",
      label: medication.text,
      genericName: medication.text,
      brandName: "",
      doseInfo: medication.dose_info,
      confidence: 90,
      reason: `medSpaCy identified "${medication.text}" as an active medication${medication.dose_info ? ` with dose ${medication.dose_info}` : ""}.`,
      relatedCodes: codes.map((code) => code.code),
      resourceType: "MedicationRequest",
      codes: codes.length > 0 ? codes : fallbackCodeForConcept(medication.text, "MEDICATION"),
    });
  });

  Object.entries(analysis.vitals || {}).forEach(([name, value], index) => {
    const label = name.replace(/_/g, " ");
    const codes = codeCandidatesForText(label, "Laboratory Tests");
    concepts.push({
      id: `medspacy-vital-${index}-${name}`,
      section: "vitals",
      label,
      units: name === "blood_pressure" ? "mmHg" : "",
      value,
      confidence: 96,
      reason: `Vital sign "${label}" was extracted only from a Vitals or Physical Exam section.`,
      relatedCodes: codes.map((code) => code.code),
      resourceType: "Observation",
      codes: codes.length > 0 ? codes : fallbackCodeForConcept(label, "OBSERVATION"),
    });
  });

  return concepts;
}

function makeFhirCoding(concept) {
  return {
    coding: concept.codes
      .filter((code) => code.systemName !== "CPT")
      .map((code) => ({
        system: code.system,
        code: code.code,
        display: code.display,
      })),
    text: concept.label,
  };
}

function buildClinicalResource(concept) {
  const coding = makeFhirCoding(concept);
  if (concept.resourceType === "MedicationRequest") {
    const resource = { resourceType: "MedicationRequest", id: concept.id, status: "active", intent: "order", medicationCodeableConcept: coding, subject: { reference: "Patient/example" } };
    if (concept.doseInfo) {
      resource.dosageInstruction = [{ text: concept.doseInfo }];
    }
    return resource;
  }
  if (concept.resourceType === "Observation") {
    return { resourceType: "Observation", id: concept.id, status: "final", code: coding, subject: { reference: "Patient/example" }, valueString: concept.value ? String(concept.value) : concept.units ? `Detected value, ${concept.units}` : "Detected value" };
  }
  if (concept.resourceType === "Procedure") {
    return { resourceType: "Procedure", id: concept.id, status: "preparation", code: coding, subject: { reference: "Patient/example" } };
  }
  return {
    resourceType: "Condition",
    id: concept.id,
    clinicalStatus: { coding: [{ system: "http://terminology.hl7.org/CodeSystem/condition-clinical", code: "active" }] },
    code: coding,
    subject: { reference: "Patient/example" },
  };
}

function buildClinicalBundle(concepts) {
  const resources = [
    { resourceType: "Patient", id: "example" },
    { resourceType: "Encounter", id: "clinical-coding-encounter", status: "finished", class: { system: "http://terminology.hl7.org/CodeSystem/v3-ActCode", code: "AMB" }, subject: { reference: "Patient/example" } },
    ...concepts.map(buildClinicalResource),
  ];
  return { resourceType: "Bundle", type: "collection", entry: resources.map((resource) => ({ resource })) };
}

function downloadTextFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function ClinicalCodingAssistant({ colors, isMobile, notify }) {
  const [clinicalText, setClinicalText] = useState(CLINICAL_SAMPLE_TEXT);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [selectedConceptId, setSelectedConceptId] = useState(null);
  const [analysisSource, setAnalysisSource] = useState("mock");
  const [backendAnalysis, setBackendAnalysis] = useState(null);
  const [analysisError, setAnalysisError] = useState("");

  // Dropdown States
  const [activeCopyDropdown, setActiveCopyDropdown] = useState(false);
  const [activeExportDropdown, setActiveExportDropdown] = useState(false);

  const copyRef = useRef(null);
  const exportRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (copyRef.current && !copyRef.current.contains(event.target)) {
        setActiveCopyDropdown(false);
      }
      if (exportRef.current && !exportRef.current.contains(event.target)) {
        setActiveExportDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const detectedConcepts = useMemo(() => {
    if (!hasAnalyzed) return [];
    if (backendAnalysis) return conceptsFromBackendAnalysis(backendAnalysis);
    return detectClinicalConcepts(clinicalText);
  }, [backendAnalysis, clinicalText, hasAnalyzed]);
  const selectedConcept = detectedConcepts.find((concept) => concept.id === selectedConceptId) || detectedConcepts[0];
  const selectedResource = selectedConcept ? buildClinicalResource(selectedConcept) : null;
  const bundle = buildClinicalBundle(detectedConcepts);

  function copyValue(label, value) {
    navigator.clipboard.writeText(value);
    notify(`Copied ${label}`, "success");
  }

  async function analyzeText() {
    if (!clinicalText.trim()) {
      notify("Paste clinical text before analyzing", "error");
      return;
    }
    setIsAnalyzing(true);
    setHasAnalyzed(false);
    setBackendAnalysis(null);
    setAnalysisError("");

    const apiKey = localStorage.getItem("smartfhirApiKey");
    const headers = {
      "Content-Type": "application/json",
      ...(apiKey ? { "X-API-Key": apiKey } : {}),
    };

    try {
      const response = await fetch(`${API_BASE}/api/clinical-note/analyze`, {
        method: "POST",
        headers,
        body: JSON.stringify({ text: clinicalText }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Clinical NLP service is unavailable.");
      }

      setBackendAnalysis(data);
      setAnalysisSource("medspacy");
      setHasAnalyzed(true);
      notify("Clinical text analyzed with medSpaCy", "success");
    } catch (error) {
      setAnalysisError(error.message);
      setAnalysisSource("mock");
      setHasAnalyzed(true);
      notify("Using local fallback analyzer", "error");
    } finally {
      setHasAnalyzed(true);
      setIsAnalyzing(false);
    }
  }

  function exportJson() {
    downloadTextFile("clinical-coding-results.json", JSON.stringify({ detectedConcepts, resources: detectedConcepts.map(buildClinicalResource), bundle }, null, 2), "application/json");
  }

  function exportCsv() {
    const rows = [["section", "concept", "code_system", "code", "display", "confidence"], ...detectedConcepts.flatMap((concept) => concept.codes.map((code) => [concept.section, concept.label, code.systemName, code.code, code.display, `${concept.confidence}%`]))];
    downloadTextFile("clinical-coding-results.csv", rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n"), "text/csv");
  }

  function exportPdfSummary() {
    const summary = ["AI Clinical Coding Assistant Summary", "", ...detectedConcepts.map((concept) => `${concept.label} (${concept.confidence}%): ${concept.codes.map((code) => `${code.systemName}: ${code.code} - ${code.display}`).join("; ")}`)].join("\n");
    downloadTextFile("clinical-coding-summary.txt", summary, "text/plain");
    notify("PDF-ready summary exported as text", "success");
  }

  const getResourceBadgeStyle = (resourceType) => {
    const styleMap = {
      Condition: { color: "#C084FC", background: "rgba(192, 132, 252, 0.15)", border: "1px solid rgba(192, 132, 252, 0.4)" }, // soft purple
      MedicationRequest: { color: "#818CF8", background: "rgba(129, 140, 248, 0.15)", border: "1px solid rgba(129, 140, 248, 0.4)" }, // soft indigo
      Observation: { color: "#FB923C", background: "rgba(251, 146, 60, 0.15)", border: "1px solid rgba(251, 146, 60, 0.4)" }, // soft orange
      Procedure: { color: "#2DD4BF", background: "rgba(45, 212, 191, 0.15)", border: "1px solid rgba(45, 212, 191, 0.4)" }, // soft teal
    };
    return styleMap[resourceType] || { color: "#34D399", background: "rgba(52, 211, 153, 0.15)", border: "1px solid rgba(52, 211, 153, 0.4)" };
  };

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 12, padding: 24, display: "grid", gap: 16 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>AI Clinical Coding Assistant</h2>
          <p style={{ color: colors.textDim, lineHeight: 1.6, margin: "8px 0 0" }}>Describe a patient's clinical scenario and automatically discover relevant medical terminology codes and FHIR resources.</p>
        </div>
        <textarea value={clinicalText} onChange={(event) => { setClinicalText(event.target.value); setHasAnalyzed(false); }} placeholder={CLINICAL_SAMPLE_TEXT} style={{ minHeight: 210, width: "100%", border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, borderRadius: 10, padding: 14, resize: "vertical", fontFamily: "inherit", lineHeight: 1.55, fontSize: 14 }} />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button onClick={analyzeText} style={{ background: colors.accent, color: "#fff", border: "none", borderRadius: 8, padding: "11px 14px", cursor: "pointer", fontWeight: 800 }}>Analyze Clinical Text</button>
          <button onClick={() => { setClinicalText(""); setHasAnalyzed(false); }} style={{ background: colors.bg, color: colors.text, border: `1px solid ${colors.border}`, borderRadius: 8, padding: "11px 14px", cursor: "pointer", fontWeight: 700 }}>Clear</button>
          <button onClick={() => { setClinicalText(CLINICAL_SAMPLE_TEXT); setHasAnalyzed(false); }} style={{ background: colors.bg, color: colors.text, border: `1px solid ${colors.border}`, borderRadius: 8, padding: "11px 14px", cursor: "pointer", fontWeight: 700 }}>Load Sample</button>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {CLINICAL_SAMPLE_INPUTS.map((sample) => (
            <button key={sample} onClick={() => { setClinicalText(sample); setHasAnalyzed(false); }} style={{ background: colors.bg, color: colors.textDim, border: `1px solid ${colors.border}`, borderRadius: 8, padding: "8px 10px", cursor: "pointer", fontSize: 12 }}>{sample}</button>
          ))}
        </div>
      </div>

      {isAnalyzing && (
        <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(3, 1fr)", gap: 12 }}>
          {[1, 2, 3].map((item) => <div key={item} style={{ height: 120, background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 12, opacity: 0.65 }} />)}
        </div>
      )}

      {!isAnalyzing && hasAnalyzed && detectedConcepts.length === 0 && (
        <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 12, padding: 24, color: colors.textDim }}>No clinical concepts detected yet. Try adding a diagnosis, symptom, medication, lab, procedure, body part, allergy, or vital sign.</div>
      )}

      {!isAnalyzing && hasAnalyzed && detectedConcepts.length > 0 && (
        <>
          {/* Status Alert Banner */}
          {analysisSource === "medspacy" ? (
            <div
              style={{
                background: "rgba(2, 44, 34, 0.2)",
                border: "1px solid rgba(6, 78, 59, 0.5)",
                color: "#34D399",
                padding: "12px",
                borderRadius: "8px",
                fontSize: 13,
                display: "flex",
                alignItems: "start",
                gap: 10,
              }}
            >
              <span style={{ fontSize: 16 }}>✨</span>
              <div style={{ display: "grid", gap: 4 }}>
                <div style={{ fontWeight: 700 }}>Analyzed by backend medSpaCy pipeline</div>
                {backendAnalysis?.negated_or_ignored?.length > 0 && (
                  <div style={{ color: "rgba(255, 255, 255, 0.6)", fontSize: 12 }}>
                    Negated or ignored context: {backendAnalysis.negated_or_ignored.join(", ")}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div
              style={{
                background: "rgba(69, 26, 3, 0.2)",
                border: "1px solid rgba(120, 53, 15, 0.5)",
                color: "#FBBF24",
                padding: "12px",
                borderRadius: "8px",
                fontSize: 13,
                display: "flex",
                alignItems: "start",
                gap: 10,
              }}
            >
              <span style={{ fontSize: 16 }}>⚠️</span>
              <div style={{ display: "grid", gap: 4 }}>
                <div style={{ fontWeight: 700 }}>Analyzed by local dictionary fallback</div>
                <div style={{ color: "rgba(255, 255, 255, 0.6)", fontSize: 12 }}>
                  {analysisError || "The backend NLP analyzer was unreachable. Displaying results using the client-side clinical mapper."}
                </div>
              </div>
            </div>
          )}

          {/* Tables block */}
          <div style={{ display: "grid", gap: 20 }}>
            {CLINICAL_SECTIONS.map((section) => {
              const concepts = detectedConcepts.filter((concept) => concept.section === section.id);
              if (concepts.length === 0) return null;
              return (
                <div
                  key={section.id}
                  style={{
                    background: colors.surface,
                    border: `1px solid ${colors.border}`,
                    borderRadius: 12,
                    padding: 20,
                    display: "grid",
                    gap: 16,
                    boxShadow: `0 2px 8px ${colors.shadow}`,
                  }}
                >
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: colors.text }}>
                    {section.title}
                  </h3>

                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 600 }}>
                      <thead>
                        <tr style={{ borderBottom: `2px solid ${colors.border}` }}>
                          <th style={{ textAlign: "left", padding: "12px 8px", color: colors.textDim, fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", width: "25%" }}>Entity / Text</th>
                          <th style={{ textAlign: "left", padding: "12px 8px", color: colors.textDim, fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", width: "35%" }}>System & Code</th>
                          <th style={{ textAlign: "center", padding: "12px 8px", color: colors.textDim, fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", width: "12%" }}>Confidence</th>
                          <th style={{ textAlign: "left", padding: "12px 8px", color: colors.textDim, fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", width: "28%" }}>Rationale / Context</th>
                        </tr>
                      </thead>
                      <tbody>
                        {concepts.map((concept) => {
                          const isSelected = selectedConcept?.id === concept.id;
                          return (
                            <tr
                              key={concept.id}
                              onClick={() => setSelectedConceptId(concept.id)}
                              style={{
                                borderBottom: `1px solid ${colors.border}`,
                                cursor: "pointer",
                                background: isSelected ? "rgba(79, 142, 247, 0.05)" : "transparent",
                                transition: "background 0.2s ease",
                              }}
                              onMouseEnter={(e) => {
                                if (!isSelected) e.currentTarget.style.background = colors.bg;
                              }}
                              onMouseLeave={(e) => {
                                if (!isSelected) e.currentTarget.style.background = "transparent";
                              }}
                            >
                              {/* Entity / Text */}
                              <td style={{ padding: "14px 8px", color: isSelected ? colors.accent : colors.text, fontWeight: 700, fontSize: 14 }}>
                                {concept.label}
                                {(concept.genericName || concept.brandName || concept.units || concept.doseInfo || concept.value) && (
                                  <div style={{ color: colors.textDim, fontSize: 11, fontWeight: 500, marginTop: 4 }}>
                                    {[
                                      concept.genericName && `Generic: ${concept.genericName}`,
                                      concept.brandName && `Brand: ${concept.brandName}`,
                                      concept.doseInfo && `Dose: ${concept.doseInfo}`,
                                      concept.value && `Value: ${concept.value}`,
                                      concept.units && `Units: ${concept.units}`
                                    ].filter(Boolean).join(" | ")}
                                  </div>
                                )}
                              </td>

                              {/* System & Code */}
                              <td style={{ padding: "14px 8px" }}>
                                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                                  {concept.codes.map((code) => (
                                    <div key={`${concept.id}-${code.systemName}`} style={{ fontSize: 13, color: colors.textDim }}>
                                      <strong style={{ color: colors.accent, fontWeight: 700 }}>{code.systemName}:</strong>{" "}
                                      <code style={{ fontFamily: "monospace", color: colors.text }}>{code.code}</code>{" "}
                                      <span style={{ fontSize: 11, opacity: 0.8 }}>• {code.display}</span>
                                    </div>
                                  ))}
                                </div>
                              </td>

                              {/* Confidence */}
                              <td style={{ padding: "14px 8px", textAlign: "center" }}>
                                <span
                                  style={{
                                    background: "rgba(52, 211, 153, 0.1)",
                                    color: colors.success,
                                    padding: "4px 10px",
                                    borderRadius: 12,
                                    fontSize: 12,
                                    fontWeight: 700,
                                    display: "inline-block",
                                  }}
                                >
                                  {concept.confidence}%
                                </span>
                              </td>

                              {/* Rationale / Context */}
                              <td style={{ padding: "14px 8px", color: colors.textDim, fontSize: 12, lineHeight: 1.5 }}>
                                {concept.reason}
                                {concept.relatedCodes && concept.relatedCodes.length > 0 && (
                                  <div style={{ color: colors.warning, fontSize: 11, marginTop: 4, fontWeight: 500 }}>
                                    Related: {concept.relatedCodes.join(", ")}
                                  </div>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>

          {/* FHIR Checklist and preview */}
          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: 16 }}>
            {/* Actionable FHIR Checklist */}
            <div
              style={{
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: 12,
                padding: 20,
                display: "flex",
                flexDirection: "column",
                gap: 16,
                boxShadow: `0 2px 8px ${colors.shadow}`,
              }}
            >
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: colors.text }}>Suggested FHIR Resources</h3>
              
              <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
                {detectedConcepts.map((concept) => {
                  const badgeStyle = getResourceBadgeStyle(concept.resourceType);
                  const isSelected = selectedConcept?.id === concept.id;
                  return (
                    <div
                      key={`resource-${concept.id}`}
                      onClick={() => setSelectedConceptId(concept.id)}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        background: colors.bg,
                        border: `1px solid ${isSelected ? colors.accent : colors.border}`,
                        borderRadius: 10,
                        padding: "12px 16px",
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) e.currentTarget.style.borderColor = colors.accent;
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) e.currentTarget.style.borderColor = colors.border;
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        {/* Resource type badge */}
                        <span
                          style={{
                            color: badgeStyle.color,
                            background: badgeStyle.background,
                            border: badgeStyle.border,
                            padding: "3px 8px",
                            borderRadius: 6,
                            fontSize: 11,
                            fontWeight: 700,
                            fontFamily: "monospace",
                          }}
                        >
                          {concept.resourceType}
                        </span>
                        <span style={{ color: colors.text, fontWeight: 600, fontSize: 14 }}>
                          {concept.label}
                        </span>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedConceptId(concept.id);
                        }}
                        style={{
                          background: isSelected ? colors.accent : colors.surface,
                          color: isSelected ? "#fff" : colors.text,
                          border: `1px solid ${isSelected ? "transparent" : colors.border}`,
                          borderRadius: 6,
                          padding: "6px 12px",
                          cursor: "pointer",
                          fontWeight: 700,
                          fontSize: 12,
                          transition: "all 0.2s ease",
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) e.currentTarget.style.background = colors.accentDim;
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) e.currentTarget.style.background = colors.surface;
                        }}
                      >
                        Generate Resource
                      </button>
                    </div>
                  );
                })}
              </div>
              
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}>
                <button
                  onClick={() => {
                    copyValue("bundle", JSON.stringify(bundle, null, 2));
                    notify("Complete bundle copied to clipboard!", "success");
                  }}
                  style={{
                    background: `linear-gradient(135deg, ${colors.success}, #10b981)`,
                    color: "#071119",
                    border: "none",
                    borderRadius: 8,
                    padding: "11px 18px",
                    cursor: "pointer",
                    fontWeight: 800,
                    fontSize: 14,
                    boxShadow: "0 4px 14px rgba(52, 211, 153, 0.2)",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  ⚡ Generate Complete Bundle
                </button>
              </div>
            </div>

            {/* FHIR Preview IDE Window */}
            <div
              style={{
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: 12,
                padding: 20,
                display: "flex",
                flexDirection: "column",
                gap: 16,
                boxShadow: `0 2px 8px ${colors.shadow}`,
              }}
            >
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: colors.text }}>FHIR Preview</h3>


              {/* IDE Code block wrapper */}
              <div style={{ display: "flex", flexDirection: "column", borderRadius: 8, overflow: "hidden", border: `1px solid ${colors.border}` }}>
                {/* Header Toolbar */}
                <div style={{ background: colors.surface, borderBottom: `1px solid ${colors.border}`, padding: "8px 14px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontFamily: "monospace", fontSize: 12, color: colors.textDim, fontWeight: 600 }}>
                    Preview: {selectedConcept && selectedConcept.id ? `${selectedConcept.id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.json` : "type-2-diabetes.json"}
                  </span>
                  <span style={{ fontSize: 11, color: colors.accent, fontWeight: 700, textTransform: "uppercase" }}>JSON</span>
                </div>
                
                {/* Code body */}
                <pre
                  style={{
                    margin: 0,
                    background: "#020617", // True dark code container panel (bg-slate-950)
                    padding: 16,
                    color: "rgba(255, 255, 255, 0.75)",
                    overflow: "auto",
                    maxHeight: 330,
                    fontSize: 12,
                    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                    lineHeight: 1.6,
                  }}
                >
                  {JSON.stringify(selectedResource || bundle, null, 2)}
                </pre>
              </div>

              {/* Consolidated Action Dropdowns */}
              <div style={{ display: "flex", gap: 10, position: "relative" }}>
                {/* Copy Dropdown */}
                <div ref={copyRef} style={{ position: "relative" }}>
                  <button
                    onClick={() => setActiveCopyDropdown(!activeCopyDropdown)}
                    style={{
                      background: colors.bg,
                      color: colors.text,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 8,
                      padding: "8px 14px",
                      cursor: "pointer",
                      fontWeight: 700,
                      fontSize: 13,
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    📋 Copy... <span style={{ fontSize: 10 }}>▼</span>
                  </button>
                  {activeCopyDropdown && (
                    <div
                      style={{
                        position: "absolute",
                        bottom: "100%",
                        left: 0,
                        marginBottom: 6,
                        background: colors.surface,
                        border: `1px solid ${colors.border}`,
                        borderRadius: 8,
                        boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
                        zIndex: 20,
                        minWidth: 160,
                        display: "flex",
                        flexDirection: "column",
                        padding: 4,
                      }}
                    >
                      <button
                        onClick={() => {
                          if (selectedConcept) copyValue("code", selectedConcept.codes[0].code);
                          setActiveCopyDropdown(false);
                        }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Copy Code
                      </button>
                      <button
                        onClick={() => {
                          if (selectedResource) copyValue("JSON", JSON.stringify(selectedResource, null, 2));
                          setActiveCopyDropdown(false);
                        }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Copy JSON
                      </button>
                      <button
                        onClick={() => {
                          if (selectedConcept) copyValue("FHIR Coding", JSON.stringify(makeFhirCoding(selectedConcept), null, 2));
                          setActiveCopyDropdown(false);
                        }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Copy FHIR Coding
                      </button>
                      <button
                        onClick={() => {
                          copyValue("bundle", JSON.stringify(bundle, null, 2));
                          setActiveCopyDropdown(false);
                        }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Copy Bundle
                      </button>
                    </div>
                  )}
                </div>

                {/* Export Dropdown */}
                <div ref={exportRef} style={{ position: "relative" }}>
                  <button
                    onClick={() => setActiveExportDropdown(!activeExportDropdown)}
                    style={{
                      background: colors.accent,
                      color: "#fff",
                      border: "none",
                      borderRadius: 8,
                      padding: "8px 14px",
                      cursor: "pointer",
                      fontWeight: 700,
                      fontSize: 13,
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    📥 Export... <span style={{ fontSize: 10 }}>▼</span>
                  </button>
                  {activeExportDropdown && (
                    <div
                      style={{
                        position: "absolute",
                        bottom: "100%",
                        left: 0,
                        marginBottom: 6,
                        background: colors.surface,
                        border: `1px solid ${colors.border}`,
                        borderRadius: 8,
                        boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
                        zIndex: 20,
                        minWidth: 160,
                        display: "flex",
                        flexDirection: "column",
                        padding: 4,
                      }}
                    >
                      <button
                        onClick={() => { exportJson(); setActiveExportDropdown(false); }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Export JSON
                      </button>
                      <button
                        onClick={() => { downloadTextFile("clinical-coding-bundle.json", JSON.stringify(bundle, null, 2), "application/fhir+json"); setActiveExportDropdown(false); }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Export FHIR Bundle
                      </button>
                      <button
                        onClick={() => { exportPdfSummary(); setActiveExportDropdown(false); }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Export PDF Summary
                      </button>
                      <button
                        onClick={() => { exportCsv(); setActiveExportDropdown(false); }}
                        style={{ background: "transparent", border: "none", color: colors.text, padding: "8px 12px", textAlign: "left", cursor: "pointer", borderRadius: 6, fontSize: 13 }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      >
                        Export CSV
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

    </div>
  );
}

function TerminologyCenterPage() {
  const navigate = useNavigate();

  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("smartfhirTheme");
    return saved || "dark";
  });
  const colors = THEMES[theme] || THEMES.dark;

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    localStorage.setItem("smartfhirTheme", newTheme);
  };

  function logout() {
    localStorage.removeItem("smartfhirApiKey");
    localStorage.removeItem("smartfhirEmail");
    localStorage.removeItem("smartfhirPlan");
    localStorage.removeItem("smartfhirUsage");
    localStorage.removeItem("smartfhirLimit");
    localStorage.removeItem("smartfhirRemaining");
    localStorage.removeItem("smartfhirLastUsed");
    notify("Logged out successfully", "success");
    navigate("/");
  }

  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilter, setActiveFilter] = useState("All");
  const [selectedResult, setSelectedResult] = useState(null);
  const [recentSearches, setRecentSearches] = useState(
    JSON.parse(localStorage.getItem("terminologyRecentSearches") || "[]")
  );
  const [favorites, setFavorites] = useState(
    JSON.parse(localStorage.getItem("terminologyFavorites") || "[]")
  );
  const [notifications, setNotifications] = useState([]);
  const [activeTab, setActiveTab] = useState("search");
  const [validatorInput, setValidatorInput] = useState("");
  const [validatorResult, setValidatorResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [aiPrompt, setAiPrompt] = useState(AI_EXAMPLE_PROMPTS[0]);
  const [aiHasSearched, setAiHasSearched] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const detailPanelRef = useRef(null);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  useEffect(() => {
    if (!selectedResult) return undefined;

    const handleOutsideClick = (event) => {
      const target = event.target;
      if (detailPanelRef.current?.contains(target)) return;
      if (target.closest?.("[data-terminology-card='true']")) return;
      setSelectedResult(null);
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [selectedResult]);

  function notify(message, type = "info") {
    const id = Date.now();
    setNotifications((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 3000);
  }

  function handleSearch(term) {
    const trimmed = term.trim();
    if (trimmed && !recentSearches.includes(trimmed)) {
      const updated = [trimmed, ...recentSearches].slice(0, 6);
      setRecentSearches(updated);
      localStorage.setItem("terminologyRecentSearches", JSON.stringify(updated));
    }
  }

  function toggleFavorite(code) {
    const updated = favorites.includes(code)
      ? favorites.filter((c) => c !== code)
      : [...favorites, code];
    setFavorites(updated);
    localStorage.setItem("terminologyFavorites", JSON.stringify(updated));
    notify(
      favorites.includes(code) ? "Removed from favorites" : "Added to favorites",
      "success"
    );
  }

  // Helper function to get count for a filter
  const getFilterCount = (filter) => {
    if (filter === "All") return ALL_RESULTS.length;
    return ALL_RESULTS.filter((result) => 
      result.system === filter || result.category === filter
    ).length;
  };

  // Filter results based on search and filter chip
  const filteredResults = ALL_RESULTS.filter((result) => {
    const matchesSearch =
      !searchTerm ||
      result.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.display.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.synonyms?.some((synonym) =>
        synonym.toLowerCase().includes(searchTerm.toLowerCase())
      );

    const matchesFilter =
      activeFilter === "All" ||
      result.system === activeFilter ||
      result.category === activeFilter;

    return matchesSearch && matchesFilter;
  });

  const aiFinderResults = useMemo(
    () => findTerminologyCodes(aiPrompt),
    [aiPrompt]
  );

  // Validator tab logic
  const validateCode = (code) => {
    if (!code.trim()) {
      notify("Please enter a code to validate", "error");
      return;
    }
    setIsValidating(true);
    setValidatorResult(null);

    setTimeout(() => {
      const found = ALL_RESULTS.find(
        (r) => r.code.toLowerCase() === code.trim().toLowerCase()
      );
      if (found) {
        setValidatorResult({ valid: true, code: found });
        notify("✓ Valid code found", "success");
      } else {
        const similar = ALL_RESULTS.filter(
          (r) =>
            r.display.toLowerCase().includes(code.toLowerCase()) ||
            r.code.includes(code)
        ).slice(0, 3);
        setValidatorResult({
          valid: false,
          code,
          suggestions: similar,
        });
        notify("✗ Code not found", "error");
      }
      setIsValidating(false);
    }, 700);
  };

  function runAiFinder() {
    const prompt = aiPrompt.trim();
    if (!prompt) {
      setAiHasSearched(false);
      notify("Describe the clinical scenario first", "error");
      return;
    }

    setAiHasSearched(true);
    handleSearch(prompt);
    notify(
      aiFinderResults.length > 0
        ? `Found ${aiFinderResults.length} candidate codes`
        : "No confident matches found",
      aiFinderResults.length > 0 ? "success" : "error"
    );
  }

  const FILTER_CHIPS_SYSTEMS = [
    "All",
    "SNOMED CT",
    "ICD-10",
    "LOINC",
    "RxNorm",
    "FHIR ValueSet",
    "Code System",
  ];

  const FILTER_CHIPS_CATEGORIES = [
    "Diagnosis",
    "Medications",
    "Laboratory Tests",
    "Procedures",
    "Imaging/Radiology",
    "Symptoms",
    "Body Systems",
    "FHIR ValueSets",
    "Code Systems",
  ];

  return (
    <div
      style={{
        height: "100vh",
        background: colors.bg,
        color: colors.text,
        fontFamily: "'Inter', system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Notifications */}
      <div
        style={{
          position: "fixed",
          right: 20,
          top: 20,
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        {notifications.map((notif) => (
          <div
            key={notif.id}
            style={{
              background:
                notif.type === "error"
                  ? colors.error + "22"
                  : notif.type === "success"
                    ? colors.success + "22"
                    : colors.accent + "22",
              border: `1px solid ${
                notif.type === "error"
                  ? colors.error + "44"
                  : notif.type === "success"
                    ? colors.success + "44"
                    : colors.accent + "44"
              }`,
              color:
                notif.type === "error"
                  ? colors.error
                  : notif.type === "success"
                    ? colors.success
                    : colors.accent,
              borderRadius: 8,
              padding: "10px 14px",
              minWidth: 250,
              animation: "slideIn 0.3s ease",
            }}
          >
            {notif.message}
          </div>
        ))}
      </div>

      {/* Static Header */}
      <header
        style={{
          flexShrink: 0,
          background: colors.surface,
          borderBottom: `1px solid ${colors.border}`,
          padding: isMobile ? "20px 16px 0" : "24px 24px 0",
          boxShadow: `0 4px 12px ${colors.shadow}`,
          zIndex: 100,
        }}
      >
        <div style={{ maxWidth: 1600, margin: "0 auto" }}>
          {/* Title Row */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
              marginBottom: 8,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <h1 style={{ margin: 0, fontSize: 32, fontWeight: 800, color: colors.text }}>
                🧬 Terminology Center
              </h1>
            </div>

            {/* Actions: Theme Toggle, Back to tools, Logout */}
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <button onClick={toggleTheme} aria-label="Toggle Theme" style={{
                width: 34, height: 34, borderRadius: 10, border: `1px solid ${colors.border}`,
                display: "grid", placeItems: "center", background: "transparent", color: colors.text,
                cursor: "pointer", transition: "all 0.2s"
              }}>
                {theme === "dark" ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                )}
              </button>
              <button onClick={() => navigate("/api-key")} style={{
                border: `1px solid ${colors.border}`, background: "transparent", color: colors.text,
                borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
              }} onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)"} onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                Manage API
              </button>
              <button onClick={() => navigate("/tools")} style={{
                border: `1px solid ${colors.border}`, background: "transparent", color: colors.text,
                borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
              }} onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)"} onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                Back to tools
              </button>
              <button onClick={logout} style={{
                border: "1px solid #ef4444", background: "transparent", color: "#ef4444",
                borderRadius: 10, padding: "8px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
              }} onMouseEnter={(e) => e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)"} onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                Logout
              </button>
            </div>
          </div>

          <p
            style={{
              color: colors.textDim,
              fontSize: 16,
              margin: "0 0 20px 0",
              maxWidth: 600,
            }}
          >
            Search, validate, map and generate medical terminology codes.
          </p>

          {/* Tabs */}
          <div
            style={{
              display: "flex",
              gap: 4,
              borderBottom: `1px solid ${colors.border}`,
              overflowX: "auto",
            }}
          >
            {[
              { id: "search", label: "Search & Browse" },
              { id: "validator", label: "Code Validator" },
              { id: "mapper", label: "Code Mapper" },
              { id: "ai", label: "Clinical Coding Assistant" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: "none",
                  border: "none",
                  borderBottom:
                    activeTab === tab.id
                      ? `2px solid ${colors.accent}`
                      : "2px solid transparent",
                  color: activeTab === tab.id ? colors.accent : colors.muted,
                  padding: "12px 16px",
                  cursor: "pointer",
                  fontSize: 14,
                  fontWeight: activeTab === tab.id ? 700 : 600,
                  marginBottom: -1,
                  transition: "all 0.2s ease",
                  whiteSpace: "nowrap",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Scrollable Content */}
      <main
        style={{
          flex: 1,
          overflowY: "auto",
          padding: isMobile ? "20px 16px 60px" : "32px 24px 60px",
          background: colors.bg,
        }}
      >
        <div style={{ maxWidth: 1600, margin: "0 auto", display: "grid", gap: 24 }}>

          {/* SEARCH & BROWSE TAB */}
          {activeTab === "search" && (
            <div style={{ display: "grid", gap: 24 }}>
              {/* Universal Search Bar */}
              <input
                type="text"
                placeholder="Search diseases, medications, lab tests, symptoms or medical codes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onBlur={() => handleSearch(searchTerm)}
                style={{
                  width: "100%",
                  padding: "14px 16px",
                  borderRadius: 12,
                  border: `1px solid ${colors.border}`,
                  background: colors.surface,
                  color: colors.text,
                  fontSize: 15,
                  fontFamily: "inherit",
                  transition: "all 0.2s ease",
                  boxShadow: `0 2px 8px ${colors.shadow}`,
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = colors.accent;
                  e.currentTarget.style.boxShadow = `0 4px 16px ${colors.shadowLight}`;
                }}
              />

              {/* Filter Chips - Row 1: Terminology Systems */}
              <div style={{ marginBottom: 8 }}>
                <div style={{
                  color: colors.muted,
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: 8,
                }}>
                  Terminology Systems
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    flexWrap: "wrap",
                  }}
                >
                  {FILTER_CHIPS_SYSTEMS.map((chip) => (
                    <FilterChip
                      key={chip}
                      label={chip}
                      active={activeFilter === chip}
                      onClick={() => setActiveFilter(chip)}
                      colors={colors}
                      count={getFilterCount(chip)}
                      variant="system"
                    />
                  ))}
                </div>
              </div>

              {/* Filter Chips - Row 2: Resource/Category Types */}
              <div>
                <div style={{
                  color: colors.muted,
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: 8,
                }}>
                  Resource / Category Types
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    flexWrap: "wrap",
                  }}
                >
                  {FILTER_CHIPS_CATEGORIES.map((chip) => (
                    <FilterChip
                      key={chip}
                      label={chip}
                      active={activeFilter === chip}
                      onClick={() => setActiveFilter(chip)}
                      colors={colors}
                      count={getFilterCount(chip)}
                      variant="category"
                    />
                  ))}
                </div>
              </div>

              {/* Results Grid */}
              <div
                style={{
                  display: isMobile
                    ? "grid"
                    : "grid",
                  gridTemplateColumns: isMobile
                    ? "1fr"
                    : selectedResult && !isMobile
                      ? "repeat(auto-fill, minmax(340px, 1fr))"
                      : "repeat(auto-fill, minmax(380px, 1fr))",
                  gap: 24,
                }}
              >
                {filteredResults.length > 0 ? (
                  filteredResults.map((result) => (
                    <TerminologyCard
                      key={result.code}
                      result={result}
                      colors={colors}
                      onSelect={setSelectedResult}
                      onCopy={(type, value) => {
                        navigator.clipboard.writeText(value);
                        notify(
                          `Copied ${type === "code" ? "code" : type === "fhir" ? "FHIR JSON" : "system URL"}!`,
                          "success"
                        );
                      }}
                      favorites={favorites}
                      onToggleFavorite={toggleFavorite}
                    />
                  ))
                ) : (
                  <div
                    style={{
                      gridColumn: "1 / -1",
                      textAlign: "center",
                      padding: "48px 24px",
                      color: colors.textDim,
                    }}
                  >
                    <div style={{ fontSize: 18, marginBottom: 8 }}>
                      No results found
                    </div>
                    <div style={{ fontSize: 14 }}>
                      Try adjusting your search or filters
                    </div>
                  </div>
                )}
              </div>

              {/* Right Panel */}
              {selectedResult && !isMobile && (
                <div
                  style={{
                    position: "fixed",
                    right: 20,
                    top: 100,
                    width: 320,
                    maxHeight: "calc(100vh - 140px)",
                    zIndex: 100,
                  }}
                >
                  <DetailPanel
                    selected={selectedResult}
                    colors={colors}
                    onClose={() => setSelectedResult(null)}
                    panelRef={detailPanelRef}
                    onCopy={(type, value) => {
                      navigator.clipboard.writeText(value);
                      notify(
                        `Copied ${type === "code" ? "code" : type === "fhir" ? "FHIR JSON" : "system URL"}!`,
                        "success"
                      );
                    }}
                  />
                </div>
              )}

              {selectedResult && isMobile && (
                <DetailPanel
                  selected={selectedResult}
                  colors={colors}
                  onClose={() => setSelectedResult(null)}
                  panelRef={detailPanelRef}
                  onCopy={(type, value) => {
                    navigator.clipboard.writeText(value);
                    notify(
                      `Copied ${type === "code" ? "code" : type === "fhir" ? "FHIR JSON" : "system URL"}!`,
                      "success"
                    );
                  }}
                />
              )}

              {/* Recent Searches */}
              {recentSearches.length > 0 && !searchTerm && (
                <div style={{ marginTop: 24 }}>
                  <div
                    style={{
                      color: colors.muted,
                      fontSize: 12,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      marginBottom: 12,
                    }}
                  >
                    Recent Searches
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      flexWrap: "wrap",
                    }}
                  >
                    {recentSearches.map((search) => (
                      <button
                        key={search}
                        onClick={() => {
                          setSearchTerm(search);
                        }}
                        style={{
                          background: colors.surface,
                          border: `1px solid ${colors.border}`,
                          color: colors.text,
                          padding: "8px 12px",
                          borderRadius: 8,
                          cursor: "pointer",
                          fontSize: 13,
                          fontWeight: 500,
                          transition: "all 0.2s ease",
                        }}
                      >
                        {search}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Favorites */}
              {favorites.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <div
                    style={{
                      color: colors.muted,
                      fontSize: 12,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      marginBottom: 12,
                    }}
                  >
                    Favorites ({favorites.length})
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: isMobile
                        ? "1fr"
                        : "repeat(auto-fill, minmax(320px, 1fr))",
                      gap: 12,
                    }}
                  >
                    {ALL_RESULTS.filter((r) => favorites.includes(r.code)).map(
                      (result) => (
                        <TerminologyCard
                          key={result.code}
                          result={result}
                          colors={colors}
                          onSelect={setSelectedResult}
                          onCopy={(type, value) => {
                            navigator.clipboard.writeText(value);
                            notify(
                              `Copied ${type === "code" ? "code" : type === "fhir" ? "FHIR JSON" : "system URL"}!`,
                              "success"
                            );
                          }}
                          favorites={favorites}
                          onToggleFavorite={toggleFavorite}
                        />
                      )
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* VALIDATOR TAB */}
          {activeTab === "validator" && (
            <div
              style={{
                display: isMobile ? "grid" : "grid",
                gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr",
                gap: 24,
                alignItems: "start",
              }}
            >
              {/* Left Column: Input Panel */}
              <div
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 12,
                  padding: 24,
                  display: "flex",
                  flexDirection: "column",
                  gap: 16,
                  boxShadow: `0 2px 8px ${colors.shadow}`,
                }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <label
                    style={{
                      display: "block",
                      color: colors.muted,
                      fontSize: 12,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                    }}
                  >
                    Enter Code
                  </label>
                  <div style={{ display: "flex", gap: 10, alignItems: "stretch" }}>
                    <input
                      type="text"
                      placeholder="e.g., 44054006, E11, 4548-4"
                      value={validatorInput}
                      onChange={(e) => setValidatorInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") validateCode(validatorInput);
                      }}
                      style={{
                        flex: 1,
                        padding: "10px 14px",
                        borderRadius: 8,
                        border: `1px solid ${colors.border}`,
                        background: colors.bg,
                        color: colors.text,
                        fontSize: 14,
                        fontFamily: "monospace",
                        transition: "all 0.2s ease",
                        boxShadow: `0 2px 8px ${colors.shadow}`,
                      }}
                    />
                    <button
                      onClick={() => validateCode(validatorInput)}
                      disabled={isValidating}
                      style={{
                        background: colors.accent,
                        color: "#fff",
                        border: "none",
                        borderRadius: 8,
                        padding: "0 20px",
                        height: 42,
                        cursor: "pointer",
                        fontWeight: 700,
                        fontSize: 14,
                        transition: "all 0.2s ease",
                        boxShadow: `0 4px 12px ${colors.shadowLight}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 8,
                      }}
                    >
                      {isValidating ? (
                        <>
                          <div className="button-spinner" />
                          <span>Validating...</span>
                        </>
                      ) : (
                        "Validate"
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Column: Result Panel (Empty, Loading, Valid, or Invalid States) */}
              <div style={{ minHeight: 220 }}>
                {/* Empty State */}
                {!validatorResult && !isValidating && (
                  <div
                    style={{
                      border: `2px dashed ${colors.border}`,
                      borderRadius: 12,
                      padding: 32,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      textAlign: "center",
                      color: colors.textDim,
                      minHeight: 220,
                    }}
                  >
                    <span style={{ fontSize: 36, marginBottom: 12 }}>🔍</span>
                    <div style={{ fontSize: 15, fontWeight: 700, color: "#FFFFFF", marginBottom: 6 }}>
                      Validation Diagnostics
                    </div>
                    <div style={{ fontSize: 13, maxWidth: 300, lineHeight: 1.5 }}>
                      Enter a medical code on the left to validate against SNOMED, LOINC, RxNorm, and ICD-10.
                    </div>
                  </div>
                )}

                {/* Loading State */}
                {isValidating && (
                  <div
                    style={{
                      background: colors.surface,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 12,
                      padding: 24,
                      minHeight: 220,
                      boxShadow: `0 2px 8px ${colors.shadow}`,
                    }}
                  >
                    <div className="skeleton-card">
                      <div className="skeleton-title shimmer" />
                      <div className="skeleton-divider" />
                      <div className="skeleton-row">
                        <div className="skeleton-label shimmer" />
                        <div className="skeleton-value shimmer" />
                      </div>
                      <div className="skeleton-row">
                        <div className="skeleton-label shimmer" />
                        <div className="skeleton-value-long shimmer" />
                      </div>
                      <div className="skeleton-row">
                        <div className="skeleton-label shimmer" />
                        <div className="skeleton-value shimmer" />
                      </div>
                    </div>
                  </div>
                )}

                {/* Valid / Invalid State */}
                {!isValidating && validatorResult && (
                  <div style={{ display: "grid", gap: 16 }}>
                    {validatorResult.valid ? (
                      <div
                        style={{
                          background: "linear-gradient(180deg, rgba(52, 211, 153, 0.05) 0%, rgba(26, 29, 39, 0) 100%)",
                          border: `1px solid ${colors.border}`,
                          borderTop: `4px solid ${colors.success}`,
                          boxShadow: "0 8px 32px 0 rgba(52, 211, 153, 0.02)",
                          borderRadius: 12,
                          padding: 24,
                          display: "grid",
                          gap: 20,
                        }}
                      >
                        <div
                          style={{
                            fontSize: 18,
                            fontWeight: 800,
                            color: colors.success,
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                          }}
                        >
                          ✔ Valid Code
                        </div>
                        <div style={{ height: 1, background: colors.border }} />

                        {/* Two-Column Grid Layout */}
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "90px 1fr",
                            rowGap: 16,
                            columnGap: 12,
                            alignItems: "baseline",
                          }}
                        >
                          <div style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: 13, fontWeight: 700 }}>Code</div>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span
                              style={{
                                color: "#FFFFFF",
                                fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                                fontSize: 15,
                                fontWeight: 700,
                              }}
                            >
                              {validatorResult.code.code}
                            </span>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(validatorResult.code.code);
                                notify("Copied code!", "success");
                              }}
                              style={{
                                background: "transparent",
                                border: "none",
                                color: colors.muted,
                                cursor: "pointer",
                                padding: "2px",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                              title="Copy code"
                            >
                              <svg
                                width="12"
                                height="12"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              >
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                              </svg>
                            </button>
                          </div>

                          <div style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: 13, fontWeight: 700 }}>
                            Display
                          </div>
                          <div style={{ color: "#FFFFFF", fontSize: 14, fontWeight: 700, lineHeight: 1.4 }}>
                            {validatorResult.code.display}
                          </div>

                          <div style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: 13, fontWeight: 700 }}>
                            System
                          </div>
                          <div>
                            <span
                              style={{
                                background: colors.accentDim,
                                color: colors.accent,
                                padding: "3px 8px",
                                borderRadius: 6,
                                fontSize: 11,
                                fontWeight: 700,
                              }}
                            >
                              {validatorResult.code.system}
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div
                        style={{
                          background: "linear-gradient(180deg, rgba(248, 113, 113, 0.05) 0%, rgba(26, 29, 39, 0) 100%)",
                          border: `1px solid ${colors.border}`,
                          borderTop: `4px solid ${colors.error}`,
                          boxShadow: "0 8px 32px 0 rgba(248, 113, 113, 0.02)",
                          borderRadius: 12,
                          padding: 24,
                          display: "grid",
                          gap: 16,
                        }}
                      >
                        <div
                          style={{
                            fontSize: 18,
                            fontWeight: 800,
                            color: colors.error,
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                          }}
                        >
                          ❌ Invalid Code
                        </div>
                        <div style={{ color: "rgba(255, 255, 255, 0.6)", fontSize: 13, lineHeight: 1.5 }}>
                          The code <code style={{ color: colors.error, fontFamily: "monospace", fontWeight: 700 }}>"{validatorResult.code}"</code> could not be resolved in any dictionary.
                        </div>

                        {validatorResult.suggestions && validatorResult.suggestions.length > 0 && (
                          <div style={{ display: "grid", gap: 10 }}>
                            <div style={{ color: "rgba(255, 255, 255, 0.4)", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                              Suggested Codes
                            </div>
                            <div style={{ display: "grid", gap: 8 }}>
                              {validatorResult.suggestions.map((sug) => (
                                <button
                                  key={sug.code}
                                  onClick={() => {
                                    setValidatorInput(sug.code);
                                    validateCode(sug.code);
                                  }}
                                  style={{
                                    background: colors.bg,
                                    border: `1px solid ${colors.border}`,
                                    borderRadius: 8,
                                    padding: "10px 14px",
                                    color: colors.text,
                                    cursor: "pointer",
                                    textAlign: "left",
                                    fontSize: 13,
                                    transition: "all 0.2s ease",
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.borderColor = colors.accent;
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.borderColor = colors.border;
                                  }}
                                >
                                  <div style={{ fontWeight: 700, color: colors.accent, fontFamily: "monospace" }}>
                                    {sug.code}
                                  </div>
                                  <div style={{ color: colors.textDim, fontSize: 12, marginTop: 4 }}>
                                    {sug.display}
                                  </div>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* MAPPER TAB */}
          {activeTab === "mapper" && (
            <div
              style={{
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: 12,
                padding: 24,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 48, marginBottom: 16 }}>🔄</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
                Code Mapper
              </div>
              <div style={{ color: colors.textDim, marginBottom: 20 }}>
                Map between terminology systems with confidence scores
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: isMobile ? "1fr" : "repeat(2, 1fr)",
                  gap: 16,
                }}
              >
                <div>
                  <label
                    style={{
                      display: "block",
                      color: colors.muted,
                      fontSize: 12,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      marginBottom: 8,
                    }}
                  >
                    Source System
                  </label>
                  <select
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: 8,
                      border: `1px solid ${colors.border}`,
                      background: colors.bg,
                      color: colors.text,
                      fontSize: 14,
                    }}
                  >
                    <option>SNOMED CT</option>
                    <option>ICD-10</option>
                    <option>LOINC</option>
                    <option>RxNorm</option>
                  </select>
                </div>
                <div>
                  <label
                    style={{
                      display: "block",
                      color: colors.muted,
                      fontSize: 12,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      marginBottom: 8,
                    }}
                  >
                    Target System
                  </label>
                  <select
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: 8,
                      border: `1px solid ${colors.border}`,
                      background: colors.bg,
                      color: colors.text,
                      fontSize: 14,
                    }}
                  >
                    <option>ICD-10</option>
                    <option>SNOMED CT</option>
                    <option>LOINC</option>
                    <option>RxNorm</option>
                  </select>
                </div>
              </div>
              <button
                style={{
                  marginTop: 16,
                  background: colors.accent,
                  color: "#fff",
                  border: "none",
                  borderRadius: 8,
                  padding: "10px 16px",
                  cursor: "pointer",
                  fontWeight: 700,
                  fontSize: 14,
                }}
              >
                Map Code
              </button>
              <div
                style={{
                  marginTop: 24,
                  color: colors.textDim,
                  fontSize: 13,
                }}
              >
                Feature coming soon with real-time mapping data
              </div>
            </div>
          )}

          {/* AI FINDER TAB */}
          {activeTab === "ai" && (
            <ClinicalCodingAssistant
              colors={colors}
              isMobile={isMobile}
              notify={notify}
            />
          )}

          {/* AI FINDER TAB */}
          {false && activeTab === "ai" && (
            <div
              style={{
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: 12,
                padding: 24,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 48, marginBottom: 16 }}>🤖</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
                AI Code Finder
              </div>
              <div style={{ color: colors.textDim, marginBottom: 20 }}>
                Describe your patient condition in natural language
              </div>
              <textarea
                placeholder="e.g., Patient has type 2 diabetes and hypertension, taking metformin 500mg daily..."
                value={aiPrompt}
                onChange={(e) => {
                  setAiPrompt(e.target.value);
                  setAiHasSearched(false);
                }}
                style={{
                  width: "100%",
                  minHeight: 120,
                  padding: "12px 14px",
                  borderRadius: 8,
                  border: `1px solid ${colors.border}`,
                  background: colors.bg,
                  color: colors.text,
                  fontSize: 14,
                  fontFamily: "inherit",
                  resize: "vertical",
                  marginBottom: 16,
                }}
              />
              <button
                onClick={runAiFinder}
                style={{
                  background: colors.accent,
                  color: "#fff",
                  border: "none",
                  borderRadius: 8,
                  padding: "10px 16px",
                  cursor: "pointer",
                  fontWeight: 700,
                  fontSize: 14,
                }}
              >
                Find Codes
              </button>
              <div
                style={{
                  marginTop: 24,
                  color: colors.textDim,
                  fontSize: 13,
                }}
              >
                {aiHasSearched
                  ? `${aiFinderResults.length} ranked matches`
                  : "Matches update as you type. Click Find Codes to save this scenario to recent searches."}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginBottom: 20 }}>
                {AI_EXAMPLE_PROMPTS.map((example) => (
                  <button
                    key={example}
                    onClick={() => {
                      setAiPrompt(example);
                      setAiHasSearched(false);
                    }}
                    style={{
                      background: colors.bg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 8,
                      color: colors.text,
                      cursor: "pointer",
                      padding: "8px 10px",
                      fontSize: 12,
                    }}
                  >
                    {example}
                  </button>
                ))}
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fill, minmax(320px, 1fr))",
                  gap: 12,
                  textAlign: "left",
                }}
              >
                {aiFinderResults.length > 0 ? (
                  aiFinderResults.map((result) => (
                    <TerminologyCard
                      key={result.code}
                      result={result}
                      colors={colors}
                      onSelect={setSelectedResult}
                      onCopy={(type, value) => {
                        navigator.clipboard.writeText(value);
                        notify(
                          `Copied ${type === "code" ? "code" : type === "fhir" ? "FHIR JSON" : "system URL"}!`,
                          "success"
                        );
                      }}
                      favorites={favorites}
                      onToggleFavorite={toggleFavorite}
                    />
                  ))
                ) : (
                  <div
                    style={{
                      background: colors.bg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 12,
                      padding: 18,
                      color: colors.textDim,
                      lineHeight: 1.6,
                      textAlign: "center",
                    }}
                  >
                    Add a diagnosis, symptom, medication, lab, or procedure to see matching codes.
                  </div>
                )}
              </div>
              {selectedResult && (
                <div style={{ marginTop: 16, textAlign: "left" }}>
                  <DetailPanel
                    selected={selectedResult}
                    colors={colors}
                    onClose={() => setSelectedResult(null)}
                    panelRef={detailPanelRef}
                    onCopy={(type, value) => {
                      navigator.clipboard.writeText(value);
                      notify(
                        `Copied ${type === "code" ? "code" : type === "fhir" ? "FHIR JSON" : "system URL"}!`,
                        "success"
                      );
                    }}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(10px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .button-spinner {
          width: 14px;
          height: 14px;
          border: 2px solid transparent;
          border-top-color: #ffffff;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        @keyframes shimmer-sweep {
          0% { background-position: -200px 0; }
          100% { background-position: 200px 0; }
        }
        .shimmer {
          background: linear-gradient(90deg, #1A1D27 25%, #2A2D3E 50%, #1A1D27 75%);
          background-size: 400px 100%;
          animation: shimmer-sweep 1.4s infinite linear;
        }
        .skeleton-card {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .skeleton-title {
          height: 24px;
          width: 120px;
          border-radius: 4px;
        }
        .skeleton-divider {
          height: 1px;
          background: #2A2D3E;
          width: 100%;
        }
        .skeleton-row {
          display: grid;
          grid-template-columns: 90px 1fr;
          gap: 12px;
          align-items: center;
        }
        .skeleton-label {
          height: 16px;
          width: 60px;
          border-radius: 4px;
        }
        .skeleton-value {
          height: 16px;
          width: 100px;
          border-radius: 4px;
        }
        .skeleton-value-long {
          height: 16px;
          width: 180px;
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}
export default TerminologyCenterPage;