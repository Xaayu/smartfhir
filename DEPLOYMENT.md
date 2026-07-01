# SmartFHIR Deployment Guide

## Overview
- **Frontend**: Vercel
- **Backend**: Render
- **Storage**: Render Disk-backed file storage (no database required)

---

## 1. Frontend Deployment (Vercel)

### Prerequisites
- Vercel account
- GitHub repository with frontend code

### Steps
1. **Push frontend code to GitHub**
   ```bash
   cd frontend/smartfhir-ui
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Select `frontend/smartfhir-ui` as the root directory
   - Configure environment variable:
     - `REACT_APP_API_BASE_URL`: Your Render backend URL (e.g., `https://smartfhir-backend.onrender.com`)
   - Click "Deploy"

3. **Update Environment Variable**
   - After backend is deployed, update `REACT_APP_API_BASE_URL` in Vercel settings

---

## 2. Backend Deployment (Render)

### Prerequisites
- Render account
- GitHub repository with backend code
- Render Disk attached at `/var/data` for persistent file storage
- API keys (Google, OpenAI, JWT secret)

### Steps
1. **Push backend code to GitHub**
   ```bash
   cd backend
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Deploy to Render**
   - Go to [render.com](https://render.com)
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `smartfhir-backend`
     - **Environment**: `Python`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add Environment Variables:
     - `USE_POSTGRES`: `false` (uses Render Disk file storage)
     - `SMARTFHIR_STORE_DIR`: `/var/data/store`
     - `API_KEY_PEPPER`: A long random secret used when hashing API keys
     - `GOOGLE_API_KEY`: Your Google AI API key
     - `JWT_SECRET`: Your JWT secret key
     - `OPENAI_API_KEY`: Your OpenAI API key (if using)
   - Attach a Render Disk:
     - **Name**: `smartfhir-data`
     - **Mount path**: `/var/data`
     - **Size**: `1 GB` or larger
   - Click "Create Web Service"

3. **Get Backend URL**
   - After deployment, Render will provide a URL like: `https://smartfhir-backend.onrender.com`
   - Use this URL for frontend configuration

---

## 3. Environment Variables

### Frontend (.env)
```env
REACT_APP_API_BASE_URL=https://smartfhir-backend.onrender.com
```

### Backend (Render Environment Variables)
- `USE_POSTGRES`: `false` when using Render Disk file storage
- `SMARTFHIR_STORE_DIR`: `/var/data/store`
- `API_KEY_PEPPER`: A long random secret used when hashing API keys
- `GOOGLE_API_KEY`: Your Google AI Studio API key
- `JWT_SECRET`: Generate a secure random string
- `OPENAI_API_KEY`: Your OpenAI API key (optional)

---

## 4. Storage

The recommended fallback while Supabase is unavailable is Render Disk file storage:

- Mount a Render Disk at `/var/data`.
- Set `SMARTFHIR_STORE_DIR=/var/data/store`.
- Keep `USE_POSTGRES=false`.

API keys, usage logs, feedback, local resource stores, and terminology caches will be written under that persistent directory. Do not store production keys in the app-local `backend/store/` directory on Render; Render's normal filesystem is ephemeral and can reset after redeploys, restarts, or instance replacement.

Supabase can still be used later by setting `USE_POSTGRES=true`, setting `SUPABASE_DB_URL`, and running `backend/supabase_schema.sql` in the Supabase SQL editor.

---

## 5. Verification

### Test Backend
```bash
curl https://smartfhir-backend.onrender.com/
```

Should return:
```json
{
  "message": "MedTechTools MVP is running",
  "endpoints": [...]
}
```

### Test Frontend
- Open your Vercel URL
- Try the unified bundle input
- Verify API calls work

---

## 6. Troubleshooting

### Backend Issues
- Check Render logs for errors
- Verify environment variables are set correctly
- For Render Disk mode, ensure `USE_POSTGRES=false`, `SMARTFHIR_STORE_DIR=/var/data/store`, and `API_KEY_PEPPER` are set

### Frontend Issues
- Check Vercel deployment logs
- Verify `REACT_APP_API_BASE_URL` is set correctly
- Check browser console for CORS errors

### Data Persistence Issues
- Check Render logs for `Using local file storage for API keys and usage: /var/data/store`
- Confirm the Render Disk is mounted at `/var/data`
- If data appears under `backend/store/`, `SMARTFHIR_STORE_DIR` is not configured correctly

---

## 7. Post-Deployment

- Monitor Render logs for errors
- Set up error monitoring (optional)
- Configure custom domains (optional)
- Set up CI/CD pipelines (optional)
- Consider migrating to Supabase for production persistence
