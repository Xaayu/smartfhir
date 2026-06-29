# SmartFHIR Deployment Guide

## Overview
- **Frontend**: Vercel
- **Backend**: Render
- **Database**: Supabase (already configured)

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
- Supabase database URL
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
     - `SUPABASE_DB_URL`: Your Supabase connection string
     - `GOOGLE_API_KEY`: Your Google AI API key
     - `JWT_SECRET`: Your JWT secret key
     - `OPENAI_API_KEY`: Your OpenAI API key (if using)
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
- `SUPABASE_DB_URL`: `postgresql://postgres:password@your-project.supabase.co:5432/postgres`
- `GOOGLE_API_KEY`: Your Google AI Studio API key
- `JWT_SECRET`: Generate a secure random string
- `OPENAI_API_KEY`: Your OpenAI API key (optional)

---

## 4. Supabase Setup (Already Done)

Your Supabase database should already have:
- `users` table
- `auth_tokens` table
- `oauth_providers` table
- `auth_audit_log` table
- `api_users` table
- `api_usage` table
- `feedback_submissions` table

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
- Ensure Supabase connection string is valid

### Frontend Issues
- Check Vercel deployment logs
- Verify `REACT_APP_API_BASE_URL` is set correctly
- Check browser console for CORS errors

### Database Issues
- Run SQL schema in Supabase SQL Editor if tables are missing
- Check Supabase connection string format

---

## 7. Post-Deployment

- Monitor Render logs for errors
- Set up error monitoring (optional)
- Configure custom domains (optional)
- Set up CI/CD pipelines (optional)
