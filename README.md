# MedTechTools

MedTechTools is a FastAPI + React platform for healthcare teams that need to validate, explain, and fix FHIR resources faster.

## Why this exists

FHIR integration work slows down when incoming data uses inconsistent field names, invalid enums, missing terminology, and unclear business rules. MedTechTools helps turn messy source data into clean, explainable FHIR output with one API call.

## Who it helps

- healthcare developers
- integration engineers
- health-tech startups
- data teams building EHR workflows

## What it does

- smart field mapping for common healthcare data aliases
- validation with human-readable explanations
- automatic fixes for common FHIR issues
- terminology lookups for LOINC, SNOMED CT, and RxNorm
- quality scoring and bundle generation for patient-focused workflows

## Project structure

- backend/ - FastAPI API, validators, terminology lookup, API key management
- frontend/smartfhir-ui/ - React landing page and UI

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Create .env from the example before using AI explanations:

```bash
copy ..\.env.example ..\.env
```

Then set GEMINI_API_KEY.

### Persistent API key storage

For production without Supabase, use Render Disk-backed JSON storage:

```bash
USE_POSTGRES=false
SMARTFHIR_STORE_DIR="/var/data/store"
API_KEY_PEPPER="long-random-secret"
ADMIN_TOKEN="your-founder-admin-token"
```

Mount a Render Disk at /var/data. This keeps API keys valid across deploys and restarts while Supabase is unavailable. If SMARTFHIR_STORE_DIR is not set, the backend falls back to backend/store/, which is only safe for local development.

### Supabase Postgres usage tracking

Supabase Postgres can also be used for API keys, rate limits, usage logging, and founder analytics.

1. Create a Supabase project.
2. Open the Supabase SQL editor.
3. Run backend/supabase_schema.sql.
4. Set these environment variables:

```bash
SUPABASE_DB_URL="your-supabase-postgres-uri"
USE_POSTGRES=true
API_KEY_PEPPER="long-random-secret"
ADMIN_TOKEN="your-founder-admin-token"
```

If USE_POSTGRES=true but SUPABASE_DB_URL is not set, the backend falls back to JSON file storage.

Founder analytics are available at:

```text
GET /admin/metrics
```

The React admin page is:

```text
/admin
```

## Frontend

```bash
cd frontend/smartfhir-ui
npm install
npm start
```

The frontend expects the backend at http://localhost:8000.

## Try it

- request a free API key
- submit a sample patient payload
- review the validation, explanation, and auto-fix output

## Notes

- do not commit .env, node_modules, build output, Python caches, or runtime JSON stores
- backend/store/ is kept with .gitkeep; JSON files are generated locally at runtime

