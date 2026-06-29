-- Supabase Database Schema for SmartFHIR Authentication
-- Run this SQL in Supabase SQL Editor to create the users table

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  auth_provider TEXT NOT NULL CHECK (auth_provider IN ('google', 'github', 'email')),
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN DEFAULT TRUE
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create index on auth_provider for statistics
CREATE INDEX IF NOT EXISTS idx_users_auth_provider ON users(auth_provider);

-- Create index on created_at for analytics
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Create tokens table for tracking active sessions
CREATE TABLE IF NOT EXISTS auth_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  access_token TEXT UNIQUE NOT NULL,
  refresh_token TEXT UNIQUE NOT NULL,
  token_type TEXT DEFAULT 'bearer',
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  refresh_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
);

-- Create index on user_id for token lookups
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id);

-- Create index on access_token for verification
CREATE INDEX IF NOT EXISTS idx_auth_tokens_access_token ON auth_tokens(access_token);

-- Create index on refresh_token for refresh operations
CREATE INDEX IF NOT EXISTS idx_auth_tokens_refresh_token ON auth_tokens(refresh_token);

-- Create OAuth provider linking table (for future feature: link multiple OAuth accounts)
CREATE TABLE IF NOT EXISTS oauth_providers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL CHECK (provider IN ('google', 'github')),
  provider_id TEXT NOT NULL,
  provider_email TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(provider, provider_id)
);

-- Create index on user_id for provider lookups
CREATE INDEX IF NOT EXISTS idx_oauth_providers_user_id ON oauth_providers(user_id);

-- Create audit log table for tracking authentication events
CREATE TABLE IF NOT EXISTS auth_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  event_type TEXT NOT NULL CHECK (event_type IN ('login', 'logout', 'token_refresh', 'token_revoke', 'signup')),
  provider TEXT,
  ip_address TEXT,
  user_agent TEXT,
  success BOOLEAN DEFAULT TRUE,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on user_id for audit logs
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_user_id ON auth_audit_log(user_id);

-- Create index on created_at for analytics
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_created_at ON auth_audit_log(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to log authentication events
CREATE OR REPLACE FUNCTION log_auth_event(
    p_user_id TEXT,
    p_event_type TEXT,
    p_provider TEXT DEFAULT NULL,
    p_ip_address TEXT DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO auth_audit_log (user_id, event_type, provider, ip_address, user_agent, success, error_message)
    VALUES (p_user_id, p_event_type, p_provider, p_ip_address, p_user_agent, p_success, p_error_message)
    RETURNING id INTO v_log_id;
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user with provider info
CREATE OR REPLACE FUNCTION get_user_with_providers(p_user_id TEXT)
RETURNS TABLE (
    id TEXT,
    email TEXT,
    name TEXT,
    auth_provider TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    providers TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.email,
        u.name,
        u.auth_provider,
        u.avatar_url,
        u.created_at,
        ARRAY_AGG(DISTINCT op.provider) FILTER (WHERE op.provider IS NOT NULL)
    FROM users u
    LEFT JOIN oauth_providers op ON u.id = op.user_id
    WHERE u.id = p_user_id
    GROUP BY u.id, u.email, u.name, u.auth_provider, u.avatar_url, u.created_at;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security (optional, for multi-tenant scenarios)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables WHERE tablename = 'users' AND rowsecurity = true
    ) THEN
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables WHERE tablename = 'auth_tokens' AND rowsecurity = true
    ) THEN
        ALTER TABLE auth_tokens ENABLE ROW LEVEL SECURITY;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables WHERE tablename = 'oauth_providers' AND rowsecurity = true
    ) THEN
        ALTER TABLE oauth_providers ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;

-- Create basic policies (allow all for now, can be restricted later)
DROP POLICY IF EXISTS "Users can read their own data" ON users;
CREATE POLICY "Users can read their own data" ON users
    FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS "Users can update their own profile" ON users;
CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (TRUE);

DROP POLICY IF EXISTS "Users can read their own tokens" ON auth_tokens;
CREATE POLICY "Users can read their own tokens" ON auth_tokens
    FOR SELECT USING (TRUE);

-- Add comments for documentation
COMMENT ON TABLE users IS 'Stores user authentication data from Google and GitHub OAuth';
COMMENT ON TABLE auth_tokens IS 'Stores active JWT access and refresh tokens';
COMMENT ON TABLE oauth_providers IS 'Links multiple OAuth accounts to the same user';
COMMENT ON TABLE auth_audit_log IS 'Audit trail for all authentication events';
COMMENT ON COLUMN users.id IS 'Unique user ID format: provider_providerId (e.g., google_123456, github_987654)';
COMMENT ON COLUMN users.auth_provider IS 'Primary authentication provider: google, github, or email';
COMMENT ON COLUMN auth_tokens.expires_at IS 'Expiration time for access token (typically 30 minutes from creation)';
COMMENT ON COLUMN auth_tokens.refresh_expires_at IS 'Expiration time for refresh token (typically 7 days from creation)';
