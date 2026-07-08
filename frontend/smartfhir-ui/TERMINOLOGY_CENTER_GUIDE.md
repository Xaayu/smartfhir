# 🧬 Terminology Center - Complete Guide

## Overview

The **Terminology Center** is a comprehensive medical terminology workspace integrated into MedTechTools. It provides healthcare developers with a unified platform to search, validate, map, and generate FHIR-compatible medical terminology codes from multiple standard systems.

---

## 🚀 Features

### 1. **Universal Search & Browse**
- **Intelligent Search Bar**: Search across all terminology systems simultaneously
  - Examples: "Diabetes", "HbA1c", "Metformin", "Hypertension", "E11", "44054006", "4548-4"
- **Multi-System Support**: 
  - SNOMED CT
  - ICD-10
  - LOINC
  - RxNorm
- **No Pre-Selection Required**: The search automatically identifies the terminology system

### 2. **Advanced Filtering**
Filter terminology codes by:
- **Terminology System**: SNOMED CT, ICD-10, LOINC, RxNorm
- **Category**: Procedures, Laboratory, Medication, Diagnosis

### 3. **Modern Result Cards**
Each terminology code displays:
- **System Badge**: Identifies the terminology system (color-coded)
- **Code**: The unique identifier (easily copyable)
- **Display Name**: Human-readable description
- **Description**: Detailed explanation of the code
- **Category**: Classification (Diagnosis, Medication, Lab, etc.)
- **One-Click Copy**: Copy code, display name, or full JSON
- **FHIR Generator**: Instantly generate FHIR-compatible JSON coding structures
- **Favorite Toggle**: Star any code for quick access

### 4. **Detail Panel (Right Sidebar)**
Click any result card to open a detailed view showing:
- **Full Description**: Complete clinical definition
- **Parents**: Hierarchical parent concepts (SNOMED CT)
- **Synonyms**: Alternative names and abbreviations
- **FHIR System URL**: Canonical terminology system URL
- **FHIR Coding Preview**: Ready-to-use JSON structure
- **One-Click JSON Copy**: Copy the entire FHIR coding object

### 5. **Code Validator Tab**
- **Paste or Type**: Enter any medical code
- **Instant Validation**: Checks if the code exists in the system
- **Results Display**:
  - ✅ **Valid**: Shows complete code details (system, display, category)
  - ❌ **Invalid**: Suggests similar codes to help find the correct one
- **Quick Selection**: Click suggested codes to validate and view details

### 6. **Code Mapper Tab** (Future Enhancement)
- Map between terminology systems with confidence scores
- Example mappings:
  - ICD-10 ↔ SNOMED CT
  - LOINC ↔ FHIR Observation
  - RxNorm ↔ Medication

### 7. **AI Code Finder Tab** (Future Enhancement)
- Describe patient conditions in natural language
- AI returns appropriate codes across systems
- Examples:
  - "Patient has diabetes" → SNOMED, ICD-10, FHIR Condition
  - "Taking Metformin" → RxNorm, FHIR Medication

### 8. **Recent Searches**
- Automatically tracks your last 6 searches
- Quick access to previously searched terminology
- Stored locally in browser

### 9. **Favorites System**
- Star any terminology code
- View all favorites in a dedicated section
- Bookmarks persist across sessions

### 10. **Copy Features**
Multiple copy options for every code:
- **Copy Code**: Just the code identifier (e.g., "44054006")
- **Copy Display**: Human-readable name
- **Copy System URL**: FHIR system URL for integration
- **Copy FHIR JSON**: Complete FHIR coding structure ready for APIs

---

## 📋 Supported Terminology Systems

### SNOMED CT (Systematized Nomenclature of Medicine)
- **URL**: http://snomed.info/sct
- **Use Case**: Clinical findings, diagnoses, procedures
- **Examples**:
  - 44054006: Type 2 diabetes mellitus
  - 38341003: Hypertension
  - 195967001: Asthma

### ICD-10 (International Classification of Diseases)
- **URL**: http://hl7.org/fhir/sid/icd-10
- **Use Case**: Diagnoses, procedures (procedural)
- **Examples**:
  - E11: Type 2 diabetes mellitus
  - I10: Essential hypertension
  - J45: Asthma

### LOINC (Logical Observation Identifiers Names and Codes)
- **URL**: http://loinc.org
- **Use Case**: Laboratory tests and clinical observations
- **Examples**:
  - 4548-4: Hemoglobin A1c
  - 2339-0: Blood Glucose
  - 8310-5: Body Temperature

### RxNorm (Medication Reference Terminology)
- **URL**: http://www.nlm.nih.gov/research/umls/rxnorm
- **Use Case**: Medications and drug products
- **Examples**:
  - 860975: Metformin 500 MG Oral Tablet
  - 1049630: Aspirin 325 MG Oral Tablet
  - 197361: Amoxicillin

---

## 🎨 UI Design

The Terminology Center follows MedTechTools' design system:
- **Dark Theme**: Professional, low-glare interface for extended use
- **Color Scheme**:
  - **Primary Accent**: #4F8EF7 (Blue)
  - **Success**: #34D399 (Teal)
  - **Error**: #F87171 (Red)
  - **Warning**: #FBBF24 (Amber)
- **Component Style**:
  - Rounded corners (8-12px border-radius)
  - Subtle shadows for depth
  - Smooth transitions (0.2-0.3s)
  - Card-based layouts

---

## 💾 Data Storage

All user data is stored locally in browser localStorage:
- **Recent Searches**: `terminologyRecentSearches` (JSON array)
- **Favorites**: `terminologyFavorites` (JSON array of codes)

No data is sent to external servers. All searches and favorites remain private.

---

## 📱 Responsive Design

- **Desktop**: Full layout with side-by-side detail panel
- **Tablet**: Adaptive grid, detail panel on demand
- **Mobile**: Single-column layout, tab-based navigation

---

## 🔄 Mock Data Structure

Each terminology entry includes:

```javascript
{
  system: "SNOMED CT",              // Terminology system name
  code: "44054006",                 // Unique identifier
  display: "Type 2 diabetes",       // Display name
  description: "...",               // Clinical description
  category: "Clinical finding",     // Classification
  fhirSystem: "http://snomed.info/sct",  // FHIR system URL
  parents: [...],                   // Parent concepts
  children: [...],                  // Child concepts
  related: [...],                   // Related concepts
  synonyms: [...]                   // Alternative names
}
```

---

## 🚦 Getting Started

### Access the Terminology Center

1. **From Dashboard**: Click "📚 Terminology Center" in the sidebar
2. **Direct URL**: Navigate to `/tools/terminology`

### Basic Workflow

1. **Search**: Enter a disease, medication, or code in the search bar
2. **Filter**: Use filter chips to narrow by system or category
3. **Select**: Click a result card to view full details
4. **Copy**: Use the copy buttons to get code in desired format
5. **Save**: Star codes to add to favorites for quick access

---

## 🔮 Future Enhancements

### Planned Features
- **Code Mapper**: Real-time mapping between terminology systems
- **AI Code Finder**: Natural language → medical codes
- **API Integration**: Connect to actual terminology services
- **Mapping Rules**: Custom mapping configurations
- **Batch Operations**: Process multiple codes at once
- **Export**: CSV/JSON export of searches and mappings
- **Sharing**: Share terminology sets with team members

### Backend Integration Points

The component is structured for easy API replacement:

```javascript
// Current: Mock data
const MOCK_TERMINOLOGY_DATA = { /* ... */ };

// Future: API calls
async function searchTerminology(query, system) {
  const res = await fetch(`/api/terminology/search`, {
    method: "POST",
    body: JSON.stringify({ query, system })
  });
  return res.json();
}
```

---

## 📊 Mock Data Available

### Included Codes

**SNOMED CT**:
- 44054006: Type 2 diabetes mellitus
- 38341003: Hypertension
- 195967001: Asthma

**ICD-10**:
- E11: Type 2 diabetes mellitus
- I10: Essential hypertension
- J45: Asthma

**LOINC**:
- 4548-4: Hemoglobin A1c
- 2339-0: Blood Glucose
- 8310-5: Body Temperature
- 718-7: Hemoglobin

**RxNorm**:
- 860975: Metformin 500 MG Oral Tablet
- 1049630: Aspirin 325 MG Oral Tablet
- 197361: Amoxicillin

---

## 🛠️ Technical Details

### Component Structure

```
TerminologyCenterPage/
├── Header (Title + Back button)
├── Tab Navigation
│   ├── Search & Browse
│   ├── Code Validator
│   ├── Code Mapper
│   └── AI Code Finder
├── Main Content Area
│   ├── Universal Search Bar
│   ├── Filter Chips
│   ├── Results Grid
│   ├── Detail Panel (Desktop)
│   ├── Recent Searches
│   └── Favorites Section
└── Notifications System
```

### Key Dependencies
- React 19+
- React Router DOM 7+
- No additional UI libraries (pure CSS)

### File Locations
- **Main Component**: `src/pages/TerminologyCenterPage.jsx`
- **Route**: `/tools/terminology` (Added to `App.js`)
- **Sidebar Link**: Dashboard navigation (Updated in `Dashboard.jsx`)

---

## 🎓 Usage Examples

### Example 1: Search for a Diagnosis Code
1. Type "Diabetes" in the search bar
2. See results from SNOMED CT (44054006) and ICD-10 (E11)
3. Click either result to view full details
4. Click "Generate FHIR" to get:
```json
{
  "coding": [{
    "system": "http://snomed.info/sct",
    "code": "44054006",
    "display": "Type 2 diabetes mellitus"
  }]
}
```

### Example 2: Validate a Code
1. Go to "Code Validator" tab
2. Paste code: `E11`
3. Click "Validate"
4. Result: ✅ Valid - Type 2 diabetes mellitus (ICD-10)

### Example 3: Find Medication Code
1. Search "Metformin"
2. Filter by "RxNorm"
3. Find code 860975
4. Click "Copy Code" or "Generate FHIR"
5. Use in FHIR Medication resource

---

## 📞 Support

For questions or issues:
1. Check the mock data in `MOCK_TERMINOLOGY_DATA`
2. Review FHIR system URLs in each entry
3. Refer to official documentation:
   - SNOMED CT: https://www.snomed.org/
   - ICD-10: https://www.cdc.gov/nchs/icd/icd10.htm
   - LOINC: https://loinc.org/
   - RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/

---

## 📄 License

Part of MedTechTools. All terminology codes are subject to their respective licensing agreements.

