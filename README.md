# MedTechTools

**AI-powered FHIR validation, mapping, and PHI de-identification API for healthcare developers.**

Stop debugging cryptic FHIR errors. MedTechTools maps your raw healthcare data to valid FHIR resources, explains every error in plain English, auto-fixes what it can, and returns a quality grade — in one API call.

🔗 **Live:** [medtechstools.vercel.app](https://medtechstools.vercel.app)  
📖 **API Docs:** [API Reference](#api-reference)  
🔑 **Get a free API key:** [medtechstools.vercel.app](https://medtechstools.vercel.app)

---

## The problem

Healthcare data comes from everywhere — CSV exports, legacy databases, JSON APIs, EHR systems. Converting it to valid FHIR is painful because:

- Validation errors are cryptic (`"Value error, Date value string does not match spec regex"`)
- Manual field mapping is tedious (`PtID` → `Patient.id`, `DOB` → `Patient.birthDate`)
- There's no standard way to explain *why* something failed or *how* to fix it
- PHI cleanup before sharing data with vendors requires custom code every time

MedTechTools solves all of this with one API.

---

## What it does

```
Raw input (any field names, any formats)
              ↓
   Map fields → Validate → Explain → Fix
              ↓
   Clean FHIR resource + quality grade
```

**Example — send this:**
```json
{
  "PtID": "P101",
  "Sex": "M",
  "DOB": "15/04/1990"
}
```

**Get back this:**
```json
{
  "fixed_resource": {
    "resourceType": "Patient",
    "id": "P101",
    "gender": "male",
    "birthDate": "1990-04-15"
  },
  "quality": { "grade": "A", "score": 85 },
  "errors": [
    {
      "field": "gender",
      "received": "M",
      "fix": "male",
      "explanation": "FHIR accepts only: male, female, other, unknown."
    },
    {
      "field": "birthDate",
      "received": "15/04/1990",
      "fix": "1990-04-15",
      "explanation": "FHIR requires date in YYYY-MM-DD format."
    }
  ]
}
```

---

## Features

| Feature | Description |
|---|---|
| **Smart field mapping** | 50+ built-in aliases (`PtID`, `DOB`, `Sex` → correct FHIR fields). Save your own. |
| **Plain English errors** | Every validation error explained in human-readable language |
| **Auto-fix engine** | Gender values, date formats, status codes fixed automatically |
| **Medical code lookup** | LOINC (lab tests) · SNOMED CT (diagnoses) · RxNorm (medications) |
| **Business rule checks** | Impossible dates, unrealistic ages, medication conflicts, date ordering |
| **Quality scoring** | A+ to D grade on every resource |
| **Bundle generation** | Map + validate + fix all resource types → one FHIR Bundle |
| **PHI de-identification** | HIPAA Safe Harbor compliant · redact / mask / pseudonymize |
| **118 tests passing** | Edge cases, boundary values, special characters, Arabic numerals |

---

## Supported FHIR Resources

| Resource | Mapping | Validation | Code Lookup | Business Rules |
|---|---|---|---|---|
| Patient | ✅ | ✅ | — | ✅ Age, dates |
| Observation | ✅ | ✅ | LOINC | ✅ Vital signs ranges |
| Condition | ✅ | ✅ | SNOMED CT | ✅ Date ordering |
| Encounter | ✅ | ✅ | — | ✅ Admission/discharge |
| MedicationRequest | ✅ | ✅ | RxNorm | ✅ Dose safety |

---

## Quick start

### 1. Get a free API key

```bash
curl -X POST https://your-backend.onrender.com/get-api-key \
  -H "Content-Type: application/json" \
  -d '{"email": "you@company.com"}'
```

Confirm the OTP sent to your email:

```bash
curl -X POST https://your-backend.onrender.com/confirm-api-key \
  -H "Content-Type: application/json" \
  -d '{"email": "you@company.com", "otp": "123456"}'
```

Response:
```json
{
  "api_key": "sk-smartfhir-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "calls_limit": 500,
  "calls_remaining": 500
}
```

### 2. Make your first API call

```bash
curl -X POST https://your-backend.onrender.com/map-and-validate \
  -H "X-API-Key: sk-smartfhir-xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "PtID": "P101",
      "Sex": "M",
      "DOB": "15/04/1990"
    },
    "resource_type": "Patient"
  }'
```

### 3. Check your usage

```bash
curl https://your-backend.onrender.com/usage \
  -H "X-API-Key: sk-smartfhir-xxxx"
```

---

## API Reference

All endpoints require `X-API-Key` header except `/get-api-key`, `/confirm-api-key`, and `/usage`.

### Patient

```
POST /map-and-validate     Map + validate + fix + score
POST /validate             Validate only
POST /explain-errors       Validate + explain in plain English
POST /autofix              Validate + auto-fix
POST /map                  Map raw fields to FHIR structure
POST /patient/register     Register patient for reference validation
```

### Observation

```
POST /observation/map-validate    Full pipeline with LOINC lookup
```

### Condition

```
POST /condition/map-validate      Full pipeline with SNOMED CT lookup
```

### Encounter

```
POST /encounter/map-validate      Full pipeline with condition cross-check
POST /encounter/register          Register encounter reason
```

### MedicationRequest

```
POST /medication/map-validate     Full pipeline with RxNorm lookup
```

### Bundle

```
POST /bundle/generate             Map + validate all resources → FHIR Bundle
POST /bundle/validate             Validate an existing FHIR Bundle
```

### PHI De-identification

```
POST /phi/deidentify              De-identify a single FHIR resource
POST /phi/deidentify-bundle       De-identify an entire FHIR Bundle
POST /phi/scan-text               Scan free text for PHI patterns
GET  /phi/modes                   List available de-identification modes
```

### Mappings

```
POST   /mappings/save             Save a custom field mapping
GET    /mappings/{resource_type}  View all mappings
DELETE /mappings/delete           Delete a custom mapping
```

### Auth

```
POST /auth/login/google           Initiate Google OAuth
POST /auth/login/github           Initiate GitHub OAuth
POST /auth/callback               Handle OAuth callback
POST /auth/refresh                Refresh access token
POST /auth/logout                 Logout
GET  /auth/me                     Get current user
```

---

## PHI De-identification

HIPAA Safe Harbor compliant. Covers all 18 identifier categories.

```bash
curl -X POST https://your-backend.onrender.com/phi/deidentify \
  -H "X-API-Key: sk-smartfhir-xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "resource": {
      "resourceType": "Patient",
      "id": "PT-2024-001",
      "name": [{"given": ["John"], "family": "Doe"}],
      "birthDate": "1985-08-15",
      "telecom": [{"system": "email", "value": "john@hospital.org"}]
    },
    "mode": "pseudonymize",
    "audit": true
  }'
```

**Three modes:**

| Mode | Example | Use case |
|---|---|---|
| `pseudonymize` | John Doe → James Wilson | Vendor testing, development |
| `mask` | John Doe → J\*\*\* D\*\* | Audit logs, partial privacy |
| `redact` | John Doe → [REDACTED] | Maximum privacy |

---

## Bundle generation

Send all your raw data in one call. Get back a complete FHIR Bundle.

```bash
curl -X POST https://your-backend.onrender.com/bundle/generate \
  -H "X-API-Key: sk-smartfhir-xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "Patient": {
      "PtID": "P101", "Sex": "M", "DOB": "15/04/1990"
    },
    "Observation": [
      {"TestName": "Blood Pressure", "Value": "120", "Unit": "mmHg", "PatientID": "P101", "Date": "2024-01-15", "Status": "final"},
      {"TestName": "Glucose", "Value": "95", "Unit": "mg/dL", "PatientID": "P101", "Date": "2024-01-15", "Status": "final"}
    ],
    "Condition": [
      {"PatientID": "P101", "Diagnosis": "Diabetes Type 2", "Status": "active", "Severity": "moderate"}
    ],
    "MedicationRequest": [
      {"PatientID": "P101", "MedicationName": "Metformin", "Status": "active", "OrderType": "order", "Dose": "500", "Unit": "mg"}
    ],
    "bundle_type": "collection"
  }'
```

---

## Auto-fix examples

| Input | Fixed |
|---|---|
| `"gender": "M"` | `"gender": "male"` |
| `"gender": "F"` | `"gender": "female"` |
| `"birthDate": "15/04/1990"` | `"birthDate": "1990-04-15"` |
| `"status": "complete"` | `"status": "final"` |
| `"status": "ongoing"` | `"clinicalStatus": "active"` |
| `"status": "prescribed"` | `"status": "active"` |
| `"severity": "serious"` | `"severity": "severe"` |
| `"verificationStatus": "yes"` | `"verificationStatus": "confirmed"` |
| `"deceased": "yes"` | `"deceasedBoolean": true` |
| `"class": "emergency"` | `"class": {"code": "EMER"}` |

---

## Quality scoring

Every resource and bundle gets a quality grade:

| Grade | Score | Meaning |
|---|---|---|
| A+ | 100% | No errors found |
| A | 85% | Errors found and all auto-fixed |
| B | 75% | Minor errors, most fixed |
| C | 60% | Some errors need manual review |
| D | 40% | Significant issues remain |

---

## Running locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- Gemini API key

### Backend

```bash
git clone https://github.com/Xaayu/smartfhir.git
cd smartfhir/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your keys

# Start server
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` for interactive API docs.

### Frontend

```bash
cd smartfhir/frontend/smartfhir-ui

npm install

# Set API URL
echo "REACT_APP_API_URL=http://localhost:8000" > .env

npm start
```

Open `http://localhost:3000`

### Environment variables

```env
# Required
GEMINI_API_KEY=your_gemini_key

# OAuth (optional for local dev)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Auth
JWT_SECRET=your_secret_here

# Email (optional — enables OTP delivery)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password
FOUNDER_EMAIL=your@email.com

# Debug (set to true for local dev without SMTP)
OTP_DEBUG_MODE=true

# Admin
ADMIN_TOKEN=your_admin_token
```

---

## Project structure

```
smartfhir/
├── backend/
│   ├── main.py                      # FastAPI app + middleware
│   ├── api_key_manager.py           # API key generation + usage tracking
│   ├── validator.py                 # Patient FHIR validator
│   ├── mapper.py                    # Field mapping engine
│   ├── explainer.py                 # Hybrid AI explain engine
│   ├── autofixer.py                 # Auto-fix engine
│   ├── bundle_generator.py          # FHIR Bundle builder
│   ├── phi_deidentifier.py          # PHI de-identification engine
│   ├── fake_data_generator.py       # Realistic fake data (Faker)
│   ├── validators/
│   │   ├── observation_validator.py
│   │   ├── condition_validator.py
│   │   ├── encounter_validator.py
│   │   └── medication_validator.py
│   ├── terminology/
│   │   ├── loinc_lookup.py          # LOINC code lookup + cache
│   │   ├── snomed_lookup.py         # SNOMED CT lookup + cache
│   │   └── rxnorm_lookup.py         # RxNorm lookup + cache
│   ├── routers/
│   │   └── phi.py                   # PHI de-identification endpoints
│   ├── mappings/
│   │   ├── built_in.json            # Patient field aliases
│   │   ├── observation_built_in.json
│   │   ├── condition_built_in.json
│   │   ├── encounter_built_in.json
│   │   └── medication_built_in.json
│   ├── store/                       # Local JSON storage
│   └── tests/                       # 118 passing tests
└── frontend/
    └── smartfhir-ui/                # React + Tailwind dashboard
```

---

## Tech stack

**Backend**
- FastAPI — REST API
- fhir.resources — FHIR schema validation
- Gemini AI — error explanation for complex cases
- Faker — realistic PHI pseudonymization
- httpx — LOINC / SNOMED / RxNorm API calls
- python-jose — JWT authentication

**Frontend**
- React
- React Router
- Tailwind CSS

**Infrastructure**
- Render — backend hosting
- Vercel — frontend hosting
- Supabase — database + auth

---

## Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific suites
pytest tests/test_mapping.py -v
pytest tests/test_pipeline.py -v
pytest tests/test_ai_mapping.py -v      # calls real Gemini API
pytest tests/test_edge_cases.py -v
pytest tests/test_edge_cases_2.py -v

# Run with timing
pytest tests/ -v --durations=10
```

**Test coverage:**
- Built-in field mapping (all 5 resources)
- User-defined mappings (save, apply, delete)
- Field normalization (uppercase, spaces, underscores)
- Full pipeline (map → validate → fix → score)
- Real Gemini AI explanations
- Null and empty values
- Numeric values as strings
- Whitespace trimming
- Special characters (O'Brien, São Paulo, García)
- Arabic-Indic numerals
- Boolean strings (yes/no/true/false/1/0)
- Leap year dates
- Future dates
- Partial dates
- Boundary values (age 120, dose 0, empty IDs)
- Reference validation (nonexistent patients)
- Concurrent duplicate registrations

---

## Roadmap

- [ ] HL7 v2 → FHIR conversion
- [ ] CSV / Excel bulk import
- [ ] AllergyIntolerance resource
- [ ] Procedure resource
- [ ] DiagnosticReport resource
- [ ] Immunization resource
- [ ] Python SDK
- [ ] JavaScript SDK
- [ ] CLI tool
- [ ] Webhook support
- [ ] Team / org accounts
- [ ] Custom business rules engine

---

## License

MIT

---

## Contributing

Issues and PRs welcome. If you work with FHIR and hit something MedTechTools handles badly — open an issue with the raw input that failed. That's the fastest way to improve it.

---

Built by [@Xaayu](https://github.com/Xaayu)