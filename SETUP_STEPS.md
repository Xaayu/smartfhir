# OAuth Authentication - Complete Setup Guide

## Quick Overview
You now have a complete OAuth authentication system with:
- ✅ Google OAuth 2.0 integration
- ✅ GitHub OAuth 2.0 integration  
- ✅ JWT token management (access & refresh tokens)
- ✅ Protected routes with ProtectedRoute component
- ✅ User authentication on Landing Page, API Key Page, and Navigation
- ✅ Beautiful login UI with social buttons

---

## Step 1: Get OAuth Credentials (15 minutes)

### 1.1 Google OAuth Setup

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)**
2. Create a new project or select existing one:
   - Click project dropdown → **New Project**
   - Name it "SmartFHIR" → **Create**

3. Enable Google+ API:
   - Left sidebar → **APIs & Services** → **Library**
   - Search "Google+ API" → **Enable**

4. Create OAuth 2.0 credentials:
   - Left sidebar → **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth 2.0 Client ID**
   - Choose **Web application**
   - Name: "SmartFHIR Local"
   - Add **Authorized JavaScript origins**:
     ```
     http://localhost:3000
     http://localhost
     ```
   - Add **Authorized redirect URIs**:
     ```
     http://localhost:3000/auth/callback
     http://localhost:3000/auth/callback/google
     ```
   - Click **Create** → **Download JSON** (optional, you'll see the credentials)

5. Copy your credentials:
   - Client ID: `ABC123...xyz`
   - Client Secret: `abc-DEF_GHI...xyz`

✅ **Save these values** - you'll need them in Step 2

---

### 1.2 GitHub OAuth Setup

1. Go to **[GitHub Developer Settings](https://github.com/settings/developers)**
   - Click **New OAuth App**

2. Fill in the form:
   - **Application name**: SmartFHIR
   - **Homepage URL**: `http://localhost:3000`
   - **Application description**: AI-powered FHIR validation
   - **Authorization callback URL**: `http://localhost:3000/auth/callback/github`
   - Click **Register application**

3. Copy your credentials:
   - **Client ID**: Displayed on page
   - **Client Secret**: Click "Generate a new client secret" → Copy it

✅ **Save these values** - you'll need them in Step 2

---

## Step 2: Configure Environment Variables (5 minutes)

### 2.1 Update Backend `.env` File

Open `smartfhir/.env` and update with your OAuth credentials:

```env
GEMINI_API_KEY="AIzaSyBnp8wHtCxtf3tihk30R5q_69NWrbFAIYc"
SUPABASE_DB_URL="postgresql://postgres:Nawabzade_09_@db.qexygssbrylcodjwctxd.supabase.co:5432/postgres"
API_KEY_PEPPER="smartfhir-pepper-8f4a9d2c7b1e6xq2026"
ADMIN_TOKEN="smartfhir-admin-9b7c4d2e1f0a6kz2026"

# ===== GOOGLE OAUTH (from Step 1.1) =====
GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID_HERE"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET_HERE"
GOOGLE_REDIRECT_URI="http://localhost:3000/auth/callback/google"

# ===== GITHUB OAUTH (from Step 1.2) =====
GITHUB_CLIENT_ID="YOUR_GITHUB_CLIENT_ID_HERE"
GITHUB_CLIENT_SECRET="YOUR_GITHUB_CLIENT_SECRET_HERE"
GITHUB_REDIRECT_URI="http://localhost:3000/auth/callback/github"

# ===== JWT CONFIG =====
SECRET_KEY="your-super-secret-key-min-32-chars-change-in-production-12345"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Replace:**
- `YOUR_GOOGLE_CLIENT_ID_HERE` → Your Google Client ID
- `YOUR_GOOGLE_CLIENT_SECRET_HERE` → Your Google Client Secret
- `YOUR_GITHUB_CLIENT_ID_HERE` → Your GitHub Client ID
- `YOUR_GITHUB_CLIENT_SECRET_HERE` → Your GitHub Client Secret

✅ **Save the file**

---

## Step 3: Install Dependencies (5 minutes)

### 3.1 Backend Dependencies

```bash
cd smartfhir/backend
pip install -r requirements.txt
```

This installs:
- ✅ `python-jose[cryptography]` - JWT tokens
- ✅ `passlib[bcrypt]` - Password hashing
- ✅ `PyJWT` - JWT encoding/decoding
- ✅ `httpx` - Async HTTP client for OAuth
- ✅ `authlib` - OAuth library support

### 3.2 Frontend Dependencies

```bash
cd smartfhir/frontend/smartfhir-ui
npm install
```

Or if already installed, just verify:
```bash
npm list react react-router-dom
```

✅ **Dependencies installed**

---

## Step 4: Start the Backend (3 minutes)

### 4.1 Terminal 1 - Start Backend

```bash
cd smartfhir/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

✅ **Backend running on http://localhost:8000**

---

## Step 5: Start the Frontend (3 minutes)

### 4.2 Terminal 2 - Start Frontend

```bash
cd smartfhir/frontend/smartfhir-ui
npm start
```

You should see:
```
webpack compiled successfully
Compiled successfully!

You can now view smartfhir-ui in the browser.

  Local:            http://localhost:3000
```

✅ **Frontend running on http://localhost:3000**

---

## Step 6: Test the Authentication System (10 minutes)

### 6.1 Test Google OAuth

1. Open **http://localhost:3000** in browser
2. Click **🔐 Sign In** in navbar OR **Continue with Google**
3. You'll be redirected to Google login
4. Sign in with your Google account
5. Authorize the app
6. You'll be redirected to `/dashboard` with your profile

✅ **Google OAuth working!**

### 6.2 Test GitHub OAuth

1. Go back to **http://localhost:3000**
2. Click **Continue with GitHub** 
3. Sign in with your GitHub account
4. Authorize the app
5. You'll be redirected to `/dashboard` with your profile

✅ **GitHub OAuth working!**

### 6.3 Test Email/OTP (Optional)

1. Click **Get free API key** on landing page
2. Enter your email → Click **Send confirmation code**
3. Check console logs for OTP (debug mode) or check email
4. Enter OTP → Click **Confirm code & get API key**
5. You'll be redirected to `/dashboard` with API key

✅ **Email/OTP authentication working!**

### 6.4 Test Protected Routes

1. Log out by clicking your profile → **Logout**
2. Try accessing `/dashboard` directly
3. You should be redirected to `/login` or landing page

✅ **Route protection working!**

### 6.5 Test Token Refresh

1. Sign in with OAuth
2. Keep the browser open for > 30 minutes
3. Try making an API call (the system auto-refreshes)
4. You should stay logged in

✅ **Token refresh working!**

---

## Step 7: Verify All Components (5 minutes)

### 7.1 Check Backend Endpoints

Open in terminal/curl:

```bash
# Get Google OAuth URL
curl http://localhost:8000/auth/login/google

# Get GitHub OAuth URL  
curl http://localhost:8000/auth/login/github

# Check your user (get from browser console after login)
curl "http://localhost:8000/auth/me?token=YOUR_ACCESS_TOKEN"
```

✅ **All endpoints responding**

### 7.2 Check Frontend Files

Verify these files exist:
```
✅ src/contexts/AuthContext.jsx
✅ src/services/AuthService.js
✅ src/pages/LoginPage.jsx
✅ src/pages/OAuthCallback.jsx
✅ src/components/ProtectedRoute.jsx
✅ src/components/UserProfile.jsx
✅ src/styles/LoginPage.css
✅ src/styles/UserProfile.css
```

### 7.3 Check Backend Files

Verify these files exist:
```
✅ backend/auth.py
✅ backend/oauth.py
✅ backend/oauth_routes.py
✅ backend/store/users.json (created after first login)
```

---

## Step 8: Production Checklist

Before deploying to production:

### Backend
- [ ] Change `SECRET_KEY` to a unique 32+ character string
- [ ] Update `.env` with production domain URLs
- [ ] Set `GOOGLE_REDIRECT_URI` to production URL
- [ ] Set `GITHUB_REDIRECT_URI` to production URL
- [ ] Update CORS in `main.py` to allow production domain
- [ ] Switch from JSON storage to a real database
- [ ] Implement token blacklisting for logout
- [ ] Add rate limiting on auth endpoints
- [ ] Use HTTPS only

### Frontend
- [ ] Update `REACT_APP_API_URL` to production backend
- [ ] Set production OAuth redirect URIs in Google/GitHub
- [ ] Test all auth flows in production
- [ ] Enable secure cookies
- [ ] Implement error logging

### OAuth Providers
- [ ] Register production URLs in Google Cloud Console
- [ ] Register production URLs in GitHub settings
- [ ] Test OAuth flow end-to-end

---

## Troubleshooting

### Error: "Invalid state parameter"
**Solution:** Make sure frontend and backend are on same domain/port. Restart both servers.

### Error: "Client not found" 
**Solution:** Verify your `CLIENT_ID` and `CLIENT_SECRET` in `.env` are correct. Copy them again from provider settings.

### Error: "No access token received"
**Solution:** 
1. Check that redirect URIs match exactly in OAuth app settings
2. Verify user clicked "Authorize" in OAuth provider
3. Check backend logs for error details

### Redirects not working
**Solution:**
1. Check that `http://localhost:3000` is registered in OAuth apps
2. Restart frontend: `npm start`
3. Clear browser cache and cookies
4. Try incognito/private mode

### CORS errors
**Solution:** Backend already configured for `http://localhost:3000`. For production, update in `main.py`:
```python
allow_origins=["http://localhost:3000", "https://yourdomain.com"]
```

### "Cannot connect to API"
**Solution:**
1. Make sure backend is running on `localhost:8000`
2. Run: `python -m uvicorn main:app --reload`
3. Check that all dependencies are installed

---

## Quick Reference - File Structure

```
smartfhir/
├── .env                                  ← Your OAuth credentials go here
├── backend/
│   ├── auth.py                          ← JWT & user management
│   ├── oauth.py                         ← OAuth providers
│   ├── oauth_routes.py                  ← OAuth endpoints
│   ├── main.py                          ← Updated with OAuth routes
│   ├── requirements.txt                 ← Updated with dependencies
│   └── store/
│       ├── users.json                   ← User data (created on first login)
│       └── ... (other stores)
├── frontend/smartfhir-ui/
│   ├── src/
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx          ← Global auth state
│   │   ├── services/
│   │   │   └── AuthService.js           ← OAuth API client
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx       ← Route protection
│   │   │   └── UserProfile.jsx          ← User info display
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx            ← OAuth login UI
│   │   │   ├── OAuthCallback.jsx        ← OAuth callback handler
│   │   │   ├── LandingPage.jsx          ← Updated with OAuth buttons
│   │   │   └── ApiKeyPage.jsx           ← Updated with OAuth buttons
│   │   ├── styles/
│   │   │   ├── LoginPage.css
│   │   │   └── UserProfile.css
│   │   └── App.js                       ← Updated with auth routes
│   └── package.json
└── AUTHENTICATION_SETUP.md              ← Full documentation
```

---

## Testing Checklist

- [ ] Google OAuth login works
- [ ] GitHub OAuth login works
- [ ] Email/OTP signup works
- [ ] Access token is stored in localStorage
- [ ] Refresh token is stored in localStorage
- [ ] User profile displays correctly
- [ ] Logout clears tokens
- [ ] Protected routes redirect unauthenticated users
- [ ] Tokens refresh automatically
- [ ] Multiple users can sign up
- [ ] User data persists after page reload
- [ ] Navigating to `/auth/callback` works
- [ ] API calls include bearer token

---

## Next Steps

1. ✅ Credentials configured
2. ✅ Dependencies installed
3. ✅ Backend running
4. ✅ Frontend running
5. ✅ OAuth flows tested
6. **Now:** Integrate with your API endpoints
   - Add `Authorization: Bearer {token}` header to API calls
   - Update protected endpoints to verify tokens
   - Return user-specific data based on authenticated user

---

## Support Resources

- **Setup Issues?** Check `AUTHENTICATION_SETUP.md`
- **Quick Reference?** Check `AUTH_QUICKSTART.md`
- **OAuth Docs:** 
  - [Google OAuth](https://developers.google.com/identity/protocols/oauth2)
  - [GitHub OAuth](https://docs.github.com/en/developers/apps/building-oauth-apps)
- **JWT Info:** [jwt.io](https://jwt.io/)

---

**You're all set! 🚀 Your authentication system is now fully functional.**
