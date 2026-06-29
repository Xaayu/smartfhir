# SmartFHIR Authentication System Setup Guide

This guide explains how to set up OAuth authentication for Google and GitHub in the SmartFHIR application.

## Table of Contents
1. [Google OAuth Setup](#google-oauth-setup)
2. [GitHub OAuth Setup](#github-oauth-setup)
3. [Environment Configuration](#environment-configuration)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Testing](#testing)

---

## Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Web application**
6. Add authorized redirect URIs:
   - `http://localhost:3000/auth/callback/google`
   - `http://localhost:3000/auth/callback`
   - (Production: `https://yourdomain.com/auth/callback/google`)

### Step 2: Get Credentials

1. Copy your **Client ID** and **Client Secret**
2. Store these securely in your `.env` file

### Step 3: Enable Google+ API

1. Go to **APIs & Services** → **Library**
2. Search for "Google+ API"
3. Click **Enable**

---

## GitHub OAuth Setup

### Step 1: Register OAuth Application

1. Go to GitHub Settings → **Developer settings** → **OAuth Apps**
2. Click **New OAuth App**
3. Fill in the application details:
   - **Application name**: SmartFHIR
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/auth/callback/github`

### Step 2: Get Credentials

1. Copy your **Client ID**
2. Generate and copy your **Client Secret**
3. Store these securely in your `.env` file

---

## Environment Configuration

### Backend `.env` File

Update your `.env` file with the following OAuth credentials:

```env
# Google OAuth
GOOGLE_CLIENT_ID="your-google-client-id-here"
GOOGLE_CLIENT_SECRET="your-google-client-secret-here"
GOOGLE_REDIRECT_URI="http://localhost:3000/auth/callback/google"

# GitHub OAuth
GITHUB_CLIENT_ID="your-github-client-id-here"
GITHUB_CLIENT_SECRET="your-github-client-secret-here"
GITHUB_REDIRECT_URI="http://localhost:3000/auth/callback/github"

# JWT Configuration
SECRET_KEY="your-super-secret-key-change-in-production-min-32-chars"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Frontend `.env` File (Optional)

Create or update `.env` in the frontend folder:

```env
REACT_APP_API_URL="http://localhost:8000"
```

---

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

The required packages are:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `PyJWT` - JWT encoding/decoding
- `httpx` - Async HTTP client for OAuth
- `requests` - HTTP requests
- `authlib` - OAuth library (optional but recommended for advanced use)

### 2. Run the Backend

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Backend OAuth Endpoints

The following endpoints are available:

- **GET** `/auth/login/{provider}` - Get OAuth authorization URL
  - Parameters: `provider` (google or github)
  - Response: Authorization URL for redirect

- **POST** `/auth/callback` - Handle OAuth callback
  - Body: `{ "provider": "google|github", "code": "...", "state": "..." }`
  - Response: `{ "access_token": "...", "refresh_token": "...", "user": {...} }`

- **POST** `/auth/refresh` - Refresh access token
  - Body: `{ "refresh_token": "..." }`
  - Response: `{ "access_token": "..." }`

- **POST** `/auth/logout` - Logout user
  - Body: `{ "token": "..." }`

- **GET** `/auth/me` - Get current user info
  - Query: `?token=...`
  - Response: User object

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend/smartfhir-ui
npm install
```

### 2. File Structure

The authentication system includes:

```
src/
├── contexts/
│   └── AuthContext.jsx         # Global auth state management
├── services/
│   └── AuthService.js           # OAuth API calls and token management
├── components/
│   ├── ProtectedRoute.jsx       # Route protection wrapper
│   └── UserProfile.jsx           # User info and logout
├── pages/
│   ├── LoginPage.jsx            # OAuth login page
│   └── OAuthCallback.jsx        # OAuth callback handler
└── styles/
    ├── LoginPage.css            # Login page styles
    └── UserProfile.css          # User profile styles
```

### 3. Run the Frontend

```bash
npm start
```

The app will open at `http://localhost:3000`

---

## Testing

### Local Testing

1. **Start Backend**:
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   cd frontend/smartfhir-ui
   npm start
   ```

3. **Test OAuth Flow**:
   - Click "Continue with Google" or "Continue with GitHub"
   - You'll be redirected to the OAuth provider
   - After authentication, you'll be redirected back to the app
   - You should see your profile and be able to access the dashboard

### Testing with Localhost

- Use `http://localhost:3000` for all redirects
- Make sure both redirect URLs are registered in OAuth apps

### Testing with Production URLs

- Update all redirect URLs in OAuth apps to your production domain
- Update `.env` files with production URLs
- Ensure HTTPS is used in production

---

## Troubleshooting

### "Invalid redirect_uri" Error

**Solution**: Make sure your redirect URIs exactly match what's registered in the OAuth app settings (including `http://` vs `https://`)

### "Client not found" Error

**Solution**: Verify your `CLIENT_ID` and `CLIENT_SECRET` are correct in the `.env` file

### Token Expired

**Solution**: The app automatically uses the refresh token to get a new access token. If refresh fails, user will be logged out.

### CORS Errors

**Solution**: Backend CORS is configured to allow `http://localhost:3000`. Update in `main.py` if needed:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    ...
)
```

---

## Production Deployment

### Security Considerations

1. **Change `SECRET_KEY`** in `.env` to a secure random string (min 32 characters)
2. **Use HTTPS** for all OAuth redirects
3. **Store secrets** in environment variables, never commit to git
4. **Use secure cookies** for sensitive data
5. **Implement rate limiting** on auth endpoints
6. **Add CORS restrictions** to your specific domain

### Database

Currently, the system stores users in `store/users.json`. For production:
- Implement a proper database (PostgreSQL, MongoDB, etc.)
- Add user session management
- Implement token blacklisting for logout

### Monitoring

- Log authentication attempts
- Monitor failed login rates
- Alert on suspicious activity

---

## Support

For issues or questions:
1. Check the [GitHub Issues](https://github.com/yourusername/smartfhir)
2. Review the [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)
3. Check provider-specific documentation:
   - [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
   - [GitHub OAuth Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
