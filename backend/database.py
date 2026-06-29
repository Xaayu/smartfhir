"""
Database module for Supabase PostgreSQL integration
Handles all user authentication data storage and retrieval
"""

import os
import psycopg
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
import json

# Database connection using Supabase URL
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "postgresql://postgres:password@localhost:5432/postgres")

def get_db_connection():
    """Get a connection to the Supabase PostgreSQL database"""
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to database: {str(e)}")

def init_database():
    """Initialize the database with required tables (if not already created)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Read and execute the SQL schema
        schema_path = os.path.join(os.path.dirname(__file__), 'supabase_auth_schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            # Execute the entire schema as one batch (PostgreSQL handles multiple statements)
            cur.execute(schema_sql)

            conn.commit()
            print("✅ Database initialized successfully")
        else:
            print("⚠️ Schema file not found. Run SQL manually in Supabase dashboard.")

    except Exception as e:
        print(f"❌ Database initialization error: {str(e)}")
    finally:
        if conn:
            conn.close()

def create_or_update_user(
    user_id: str,
    email: str,
    name: str,
    auth_provider: str,
    avatar_url: Optional[str] = None
) -> Dict:
    """Create or update a user in the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Upsert user (insert or update if exists)
        cur.execute("""
            INSERT INTO users (id, email, name, auth_provider, avatar_url, last_login)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                name = EXCLUDED.name,
                avatar_url = EXCLUDED.avatar_url,
                last_login = NOW(),
                updated_at = NOW()
            RETURNING id, email, name, auth_provider, avatar_url, created_at;
        """, (user_id, email, name, auth_provider, avatar_url))
        
        result = cur.fetchone()
        conn.commit()
        
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "name": result[2],
                "auth_provider": result[3],
                "avatar_url": result[4],
                "created_at": result[5].isoformat() if result[5] else None
            }
        
        return None
    
    except Exception as e:
        print(f"❌ Error creating/updating user: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_user(user_id: str) -> Optional[Dict]:
    """Get a user by ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, name, auth_provider, avatar_url, created_at, updated_at, is_active
            FROM users
            WHERE id = %s;
        """, (user_id,))
        
        result = cur.fetchone()
        
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "name": result[2],
                "auth_provider": result[3],
                "avatar_url": result[4],
                "created_at": result[5].isoformat() if result[5] else None,
                "updated_at": result[6].isoformat() if result[6] else None,
                "is_active": result[7]
            }
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching user: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get a user by email"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, name, auth_provider, avatar_url, created_at, updated_at, is_active
            FROM users
            WHERE email = %s;
        """, (email.lower(),))
        
        result = cur.fetchone()
        
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "name": result[2],
                "auth_provider": result[3],
                "avatar_url": result[4],
                "created_at": result[5].isoformat() if result[5] else None,
                "updated_at": result[6].isoformat() if result[6] else None,
                "is_active": result[7]
            }
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching user by email: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def store_token(
    user_id: str,
    access_token: str,
    refresh_token: str,
    access_token_expires_in_minutes: int = 30,
    refresh_token_expires_in_days: int = 7
) -> Optional[Dict]:
    """Store tokens in the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=access_token_expires_in_minutes)
        refresh_expires_at = now + timedelta(days=refresh_token_expires_in_days)
        
        cur.execute("""
            INSERT INTO auth_tokens (user_id, access_token, refresh_token, expires_at, refresh_expires_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, user_id, token_type, expires_at, refresh_expires_at;
        """, (user_id, access_token, refresh_token, expires_at, refresh_expires_at))
        
        result = cur.fetchone()
        conn.commit()
        
        if result:
            return {
                "id": str(result[0]),
                "user_id": result[1],
                "token_type": result[2],
                "expires_at": result[3].isoformat(),
                "refresh_expires_at": result[4].isoformat()
            }
        
        return None
    
    except Exception as e:
        print(f"❌ Error storing token: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_token(access_token: str) -> Optional[Dict]:
    """Get a token from the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, user_id, access_token, refresh_token, token_type, expires_at, refresh_expires_at, is_active
            FROM auth_tokens
            WHERE access_token = %s AND is_active = TRUE;
        """, (access_token,))
        
        result = cur.fetchone()
        
        if result:
            return {
                "id": str(result[0]),
                "user_id": result[1],
                "access_token": result[2],
                "refresh_token": result[3],
                "token_type": result[4],
                "expires_at": result[5].isoformat(),
                "refresh_expires_at": result[6].isoformat(),
                "is_active": result[7]
            }
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching token: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def revoke_token(access_token: str) -> bool:
    """Revoke a token"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE auth_tokens
            SET is_active = FALSE, updated_at = NOW()
            WHERE access_token = %s;
        """, (access_token,))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"❌ Error revoking token: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def revoke_user_tokens(user_id: str) -> bool:
    """Revoke all tokens for a user (logout)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE auth_tokens
            SET is_active = FALSE, updated_at = NOW()
            WHERE user_id = %s;
        """, (user_id,))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"❌ Error revoking user tokens: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def log_auth_event(
    user_id: Optional[str],
    event_type: str,
    provider: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> bool:
    """Log an authentication event for audit purposes"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO auth_audit_log (user_id, event_type, provider, ip_address, user_agent, success, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (user_id, event_type, provider, ip_address, user_agent, success, error_message))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"⚠️ Error logging auth event: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def link_oauth_provider(user_id: str, provider: str, provider_id: str, provider_email: Optional[str] = None) -> bool:
    """Link an OAuth provider to a user (for future multi-provider support)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO oauth_providers (user_id, provider, provider_id, provider_email)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (provider, provider_id) DO NOTHING;
        """, (user_id, provider, provider_id, provider_email))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"❌ Error linking OAuth provider: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def get_stats() -> Dict:
    """Get authentication statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total users
        cur.execute("SELECT COUNT(*) FROM users;")
        total_users = cur.fetchone()[0]
        
        # Users by provider
        cur.execute("SELECT auth_provider, COUNT(*) FROM users GROUP BY auth_provider;")
        users_by_provider = {row[0]: row[1] for row in cur.fetchall()}
        
        # Active tokens
        cur.execute("SELECT COUNT(*) FROM auth_tokens WHERE is_active = TRUE;")
        active_tokens = cur.fetchone()[0]
        
        # Today's logins
        cur.execute("""
            SELECT COUNT(*) FROM auth_audit_log 
            WHERE event_type = 'login' AND success = TRUE 
            AND created_at >= NOW() - INTERVAL '24 hours';
        """)
        logins_today = cur.fetchone()[0]
        
        return {
            "total_users": total_users,
            "users_by_provider": users_by_provider,
            "active_tokens": active_tokens,
            "logins_today": logins_today
        }
    
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
        return {}
    finally:
        if conn:
            conn.close()
