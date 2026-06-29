# OAuth Setup - Quick Command Reference

## 📋 Copy-Paste Commands (In Order)

### 1️⃣ GET CREDENTIALS (Do in Browser)

**Google:**
```
Visit: https://console.cloud.google.com/
1. Create project → "SmartFHIR"
2. APIs & Services → Enable "Google+ API"
3. Credentials → Create "OAuth 2.0 Client ID" (Web)
4. Authorized URIs:
   http://localhost:3000/auth/callback
   http://localhost:3000/auth/callback/google
5. Copy: Client ID and Client Secret
```

**GitHub:**
```
Visit: https://github.com/settings/developers
1. New OAuth App
2. Name: SmartFHIR
3. Homepage: http://localhost:3000
4. Callback: http://localhost:3000/auth/callback/github
5. Copy: Client ID and Client Secret
```

---

### 2️⃣ UPDATE .env FILE

```bash
# Edit: smartfhir/.env
# Replace these:

GOOGLE_CLIENT_ID="YOUR_GOOGLE_ID"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_SECRET"
GITHUB_CLIENT_ID="YOUR_GITHUB_ID"  
GITHUB_CLIENT_SECRET="YOUR_GITHUB_SECRET"
SECRET_KEY="your-random-32-char-secret-key-here"
```

---

### 3️⃣ TERMINAL 1 - BACKEND

```bash
cd smartfhir/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

**Wait for:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

### 4️⃣ TERMINAL 2 - FRONTEND

```bash
cd smartfhir/frontend/smartfhir-ui
npm install
npm start
```

**Wait for:**
```
Compiled successfully!
You can now view smartfhir-ui in the browser.
Local: http://localhost:3000
```

---

### 5️⃣ TEST IN BROWSER

**Open:** `http://localhost:3000`

**Test Google OAuth:**
```
Click: "🔐 Sign In" OR "Continue with Google"
→ Sign in with Google account
→ Click "Authorize"
→ Should see dashboard with profile
✅ SUCCESS
```

**Test GitHub OAuth:**
```
Go back to landing page
Click: "Continue with GitHub"
→ Sign in with GitHub account
→ Click "Authorize"  
→ Should see dashboard with profile
✅ SUCCESS
```

**Test Logout:**
```
Click profile → Logout
Try to access http://localhost:3000/dashboard
→ Should redirect to login/landing
✅ SUCCESS
```

---

## 🔍 Verification Checklist

```bash
# ✅ Check Backend
curl http://localhost:8000/auth/login/google

# ✅ Check Frontend
npm list react-router-dom

# ✅ Check Python packages
pip list | grep -E "python-jose|PyJWT"

# ✅ Check .env exists
cat smartfhir/.env | grep GOOGLE_CLIENT_ID

# ✅ Check files exist
ls smartfhir/backend/auth.py
ls smartfhir/backend/oauth.py
ls smartfhir/backend/oauth_routes.py
ls smartfhir/frontend/smartfhir-ui/src/contexts/AuthContext.jsx
ls smartfhir/frontend/smartfhir-ui/src/services/AuthService.js
```

---

## 🆘 Common Issues & Fixes

### Issue: "Cannot connect to localhost:8000"
```bash
# Fix: Make sure backend is running
cd smartfhir/backend
python -m uvicorn main:app --reload
```

### Issue: "Invalid state parameter"
```bash
# Fix: Restart both services
# Terminal 1: Ctrl+C in backend, run python -m uvicorn main:app --reload
# Terminal 2: Ctrl+C in frontend, run npm start
```

### Issue: "GOOGLE_CLIENT_ID not found"
```bash
# Fix: Update .env file with credentials from Google Cloud Console
nano smartfhir/.env
# OR edit in VS Code
```

### Issue: "Dependencies missing"
```bash
# Backend
cd smartfhir/backend
pip install -r requirements.txt

# Frontend
cd smartfhir/frontend/smartfhir-ui
npm install
```

### Issue: OAuth says "Redirect URI mismatch"
```bash
# Fix: Add this URI to your OAuth app settings:
http://localhost:3000/auth/callback
http://localhost:3000/auth/callback/google  (for Google)
http://localhost:3000/auth/callback/github  (for GitHub)
```

---

## 📁 Key File Locations

```
smartfhir/
├── .env                              ← YOUR CREDENTIALS GO HERE
├── SETUP_STEPS.md                   ← Detailed guide
├── EXECUTION_GUIDE.md               ← Workflow & testing
├── backend/
│   ├── auth.py                      ← JWT logic
│   ├── oauth.py                     ← OAuth providers
│   ├── oauth_routes.py              ← OAuth endpoints
│   ├── main.py                      ← Updated with auth
│   └── requirements.txt             ← Updated dependencies
└── frontend/smartfhir-ui/src/
    ├── contexts/AuthContext.jsx     ← Auth state
    ├── services/AuthService.js      ← OAuth API client
    ├── pages/LoginPage.jsx          ← Login UI
    └── App.js                       ← Updated routing
```

---

## 🚀 One-Minute Summary

1. **Get OAuth credentials** from Google & GitHub
2. **Put them in** `.env` file
3. **Terminal 1:** `cd smartfhir/backend` → `python -m uvicorn main:app --reload`
4. **Terminal 2:** `cd smartfhir/frontend/smartfhir-ui` → `npm start`
5. **Browser:** Open `http://localhost:3000`
6. **Click:** "Continue with Google" or "Continue with GitHub"
7. **Sign in** with your account
8. **✅ Done!** You're authenticated

---

## 📞 Need Help?

- **Detailed Setup?** → Read `SETUP_STEPS.md`
- **Complete Workflow?** → Read `EXECUTION_GUIDE.md`
- **Quick Reference?** → This file (`COMMANDS.md`)
- **API Documentation?** → Read `AUTH_QUICKSTART.md`
- **Full Setup Info?** → Read `AUTHENTICATION_SETUP.md`

---

## ⏱️ Time Estimates

| Task | Time |
|------|------|
| Get OAuth credentials | 10 min |
| Update .env file | 2 min |
| Install dependencies | 5 min |
| Start backend | 1 min |
| Start frontend | 1 min |
| Test OAuth flows | 10 min |
| **TOTAL** | **~30 min** |

---

## ✅ Success Indicators

- ✅ Backend running without errors
- ✅ Frontend running without errors  
- ✅ Can sign in with Google
- ✅ Can sign in with GitHub
- ✅ User profile displays
- ✅ Logout works
- ✅ Protected routes work

**All green? You're done! 🎉**

---

## 🔐 Security Notes

For production:
- [ ] Use HTTPS (not HTTP)
- [ ] Change SECRET_KEY to unique 32+ char string
- [ ] Use real database (not JSON)
- [ ] Set up HTTPS redirect URIs in OAuth apps
- [ ] Enable CORS only for your domain
- [ ] Use secure cookies
- [ ] Implement rate limiting
- [ ] Add token blacklisting

---

## 📚 Documentation Files

```
SETUP_STEPS.md         ← Step-by-step complete setup
EXECUTION_GUIDE.md     ← Detailed workflow & testing
COMMANDS.md            ← This file (quick commands)
AUTHENTICATION_SETUP.md ← Full reference guide
AUTH_QUICKSTART.md     ← API reference & examples
```

**Pick the guide that matches your learning style!**

---

**Ready to start? Jump to Step 1! 🚀**
