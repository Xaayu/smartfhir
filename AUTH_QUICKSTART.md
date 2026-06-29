# OAuth Authentication System - Quick Start

## Overview

SmartFHIR now includes a complete OAuth 2.0 authentication system supporting:
- ✅ **Google OAuth 2.0**
- ✅ **GitHub OAuth 2.0**
- ✅ **JWT Token Management** (Access & Refresh tokens)
- ✅ **Protected Routes**
- ✅ **User Profile Management**

## Components Added

### Backend (`smartfhir/backend/`)

1. **`auth.py`** - JWT token creation, verification, and user management
2. **`oauth.py`** - OAuth provider implementations (Google & GitHub)
3. **`oauth_routes.py`** - Authentication endpoints
4. Updated `main.py` - Integrated OAuth routes and middleware

### Frontend (`smartfhir/frontend/smartfhir-ui/src/`)

1. **`contexts/AuthContext.jsx`** - Global authentication state management
2. **`services/AuthService.js`** - OAuth API client
3. **`components/ProtectedRoute.jsx`** - Route protection
4. **`components/UserProfile.jsx`** - User info display
5. **`pages/LoginPage.jsx`** - OAuth login UI
6. **`pages/OAuthCallback.jsx`** - OAuth callback handler
7. **`styles/LoginPage.css`** - Login page styling
8. **`styles/UserProfile.css`** - User profile styling

## Quick Start (5 Minutes)

### 1. Get OAuth Credentials

**Google:**
- Visit: https://console.developers.google.com/
- Create OAuth 2.0 Client ID (Web application)
- Note: Client ID and Client Secret

**GitHub:**
- Visit: https://github.com/settings/developers
- Create new OAuth App
- Note: Client ID and Client Secret

### 2. Configure Environment

**`.env` file in `backend/` folder:**
```env
# Google OAuth
GOOGLE_CLIENT_ID="your_google_client_id"
GOOGLE_CLIENT_SECRET="your_google_client_secret"

# GitHub OAuth
GITHUB_CLIENT_ID="your_github_client_id"
GITHUB_CLIENT_SECRET="your_github_client_secret"

# JWT
SECRET_KEY="your-secret-key-at-least-32-chars"
```

### 3. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend/smartfhir-ui
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend/smartfhir-ui
npm start
```

### 5. Test Authentication

1. Open http://localhost:3000
2. Click "Continue with Google" or "Continue with GitHub"
3. Complete OAuth flow
4. You'll be redirected to the dashboard with your profile

## API Endpoints

### Authentication Endpoints

```
GET  /auth/login/{provider}              # Get OAuth authorization URL
POST /auth/callback                       # Handle OAuth callback
POST /auth/refresh                        # Refresh access token
POST /auth/logout                         # Logout user
GET  /auth/me?token={token}              # Get current user
```

### Request Examples

**Get Google Login URL:**
```bash
curl http://localhost:8000/auth/login/google
```

**Handle Callback:**
```bash
curl -X POST http://localhost:8000/auth/callback \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "code": "auth_code_from_google",
    "state": "state_value"
  }'
```

**Refresh Token:**
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'
```

## Frontend Usage

### Using AuthContext Hook

```jsx
import { useAuth } from "./contexts/AuthContext";

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();

  return (
    <div>
      {isAuthenticated ? (
        <>
          <p>Welcome, {user.name}!</p>
          <button onClick={logout}>Logout</button>
        </>
      ) : (
        <button onClick={() => login("google")}>Login with Google</button>
      )}
    </div>
  );
}
```

### Using AuthService Directly

```jsx
import AuthService from "./services/AuthService";

// Check if authenticated
if (AuthService.isAuthenticated()) {
  const token = AuthService.getAccessToken();
  const user = AuthService.getStoredUser();
}

// Make authenticated request
const response = await fetch("http://localhost:8000/api/data", {
  headers: {
    "Authorization": `Bearer ${AuthService.getAccessToken()}`
  }
});
```

### Protected Routes

```jsx
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";

<Routes>
  <Route 
    path="/dashboard" 
    element={
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    } 
  />
</Routes>
```

## Token Management

### Access Token
- Expires in: 30 minutes (configurable)
- Used for: API requests
- Stored in: localStorage
- Header: `Authorization: Bearer {token}`

### Refresh Token
- Expires in: 7 days (configurable)
- Used for: Getting new access token
- Stored in: localStorage (secure)

### Automatic Refresh
The system automatically refreshes tokens when they expire using the refresh token.

## User Storage

Currently, users are stored in `store/users.json`:

```json
{
  "google_123456789": {
    "id": "google_123456789",
    "email": "user@gmail.com",
    "name": "John Doe",
    "auth_provider": "google",
    "avatar_url": "https://...",
    "created_at": "2024-01-01T..."
  },
  "github_987654": {
    "id": "github_987654",
    "email": "user@github.com",
    "name": "Jane Doe",
    "auth_provider": "github",
    "avatar_url": "https://...",
    "created_at": "2024-01-01T..."
  }
}
```

**For production**, migrate to a proper database (PostgreSQL, MongoDB, etc.)

## Security Features

✅ **JWT Tokens** - Stateless authentication
✅ **CORS Protection** - Configured origins only
✅ **State Parameter** - CSRF protection in OAuth flow
✅ **Token Expiration** - Automatic token refresh
✅ **Secure Storage** - Tokens in localStorage (can be enhanced)
✅ **Protected Routes** - Prevents unauthorized access

## Troubleshooting

### "Invalid state parameter"
- Ensure both frontend and backend are on the same domain/port
- Check that state values match between request and response

### "No access token received"
- Verify OAuth credentials in `.env`
- Check OAuth app settings for correct redirect URIs
- Ensure user authorizes the application

### CORS errors
- Frontend must be on http://localhost:3000
- Backend allows this in main.py middleware
- Update allowed origins for production

## Next Steps

1. **Customize Login UI** - Modify `LoginPage.jsx` styling
2. **Add User Roles** - Implement role-based access control
3. **Database Integration** - Replace `store/users.json` with a database
4. **Email Verification** - Add email confirmation flow
5. **Social Linking** - Allow users to link multiple OAuth providers

## File Structure

```
smartfhir/
├── backend/
│   ├── auth.py                  # Auth logic
│   ├── oauth.py                 # OAuth providers
│   ├── oauth_routes.py          # Auth endpoints
│   ├── main.py                  # Updated with OAuth
│   ├── requirements.txt         # Updated dependencies
│   └── store/
│       └── users.json           # User data
├── frontend/smartfhir-ui/src/
│   ├── contexts/
│   │   └── AuthContext.jsx
│   ├── services/
│   │   └── AuthService.js
│   ├── components/
│   │   ├── ProtectedRoute.jsx
│   │   └── UserProfile.jsx
│   ├── pages/
│   │   ├── LoginPage.jsx
│   │   └── OAuthCallback.jsx
│   ├── styles/
│   │   ├── LoginPage.css
│   │   └── UserProfile.css
│   └── App.js                   # Updated with auth routes
└── AUTHENTICATION_SETUP.md      # Full setup guide
```

## Support & Resources

- **Setup Guide**: See `AUTHENTICATION_SETUP.md`
- **Google OAuth Docs**: https://developers.google.com/identity
- **GitHub OAuth Docs**: https://docs.github.com/en/developers/apps/building-oauth-apps
- **JWT Info**: https://jwt.io/

---

**Happy authenticating! 🔐**
