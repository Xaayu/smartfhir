# MedTechTools

MedTechTools is a FastAPI + React app for mapping, validating, explaining, and auto-fixing common FHIR resources.

## Structure

- `backend/` - FastAPI API, validators, terminology lookup, API key management
- `frontend/smartfhir-ui/` - React landing page and UI

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Create `.env` from the example before using AI explanations:

```bash
copy ..\.env.example ..\.env
```

Then set `GEMINI_API_KEY`.

### Persistent API key storage

For production without Supabase, use Render Disk-backed JSON storage:

```bash
USE_POSTGRES=false
SMARTFHIR_STORE_DIR="/var/data/store"
API_KEY_PEPPER="long-random-secret"
ADMIN_TOKEN="your-founder-admin-token"
```

Mount a Render Disk at `/var/data`. This keeps API keys valid across deploys and restarts while Supabase is unavailable. If `SMARTFHIR_STORE_DIR` is not set, the backend falls back to `backend/store/`, which is only safe for local development.

### Supabase Postgres usage tracking

Supabase Postgres can also be used for API keys, rate limits, usage logging, and founder analytics.

1. Create a Supabase project.
2. Open the Supabase SQL editor.
3. Run `backend/supabase_schema.sql`.
4. Set these environment variables:

```bash
SUPABASE_DB_URL="your-supabase-postgres-uri"
USE_POSTGRES=true
API_KEY_PEPPER="long-random-secret"
ADMIN_TOKEN="your-founder-admin-token"
```

If `USE_POSTGRES=true` but `SUPABASE_DB_URL` is not set, the backend falls back to JSON file storage.

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

The frontend expects the backend at `http://localhost:8000`.

## Notes

- Do not commit `.env`, `node_modules`, build output, Python caches, or runtime JSON stores.
- `backend/store/` is kept with `.gitkeep`; JSON files are generated locally at runtime.

