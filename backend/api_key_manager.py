import hashlib
import json
import os
import secrets
import string
from datetime import datetime, timezone

from dotenv import load_dotenv

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # Keeps local file fallback usable before deps are installed.
    psycopg = None
    dict_row = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
KEYS_PATH = os.path.join(BASE_DIR, "store", "keys.json")
USAGE_PATH = os.path.join(BASE_DIR, "store", "usage.jsonl")
MONTHLY_LIMIT = 500

load_dotenv(os.path.join(PROJECT_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def database_url() -> str:
    return os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or ""


def use_postgres() -> bool:
    # Explicitly disable PostgreSQL - force file storage mode
    return False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def hash_key(api_key: str) -> str:
    pepper = os.getenv("API_KEY_PEPPER", "")
    return hashlib.sha256(f"{pepper}{api_key}".encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    chars = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(32))
    return f"sk_live_{random_part}"


def db_connect():
    return psycopg.connect(database_url(), row_factory=dict_row)


def current_month_bounds() -> tuple[datetime, datetime]:
    now = utc_now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def load_keys() -> dict:
    if os.path.exists(KEYS_PATH):
        with open(KEYS_PATH, "r") as f:
            keys = json.load(f)
            if isinstance(keys, str):
                keys = json.loads(keys)
            if isinstance(keys, dict):
                return keys
    return {}


def save_keys(keys: dict):
    os.makedirs(os.path.dirname(KEYS_PATH), exist_ok=True)
    with open(KEYS_PATH, "w") as f:
        json.dump(keys, f, indent=2)


def create_key(email: str) -> dict:
    if use_postgres():
        return create_key_db(email)
    return create_key_file(email)


def create_key_db(email: str) -> dict:
    clean_email = email.lower().strip()
    api_key = generate_api_key()
    api_key_hash = hash_key(api_key)

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into api_users (email, api_key_hash, api_key_preview, plan, monthly_limit, active)
                values (%s, %s, %s, 'Free', %s, true)
                on conflict (email) do update set
                    api_key_hash = excluded.api_key_hash,
                    api_key_preview = excluded.api_key_preview,
                    active = true,
                    updated_at = now()
                returning id, email, plan, monthly_limit, created_at
                """,
                (clean_email, api_key_hash, f"{api_key[:12]}...{api_key[-4:]}", MONTHLY_LIMIT),
            )
            user = cur.fetchone()

    return {
        "already_exists": False,
        "api_key": api_key,
        "email": user["email"],
        "plan": user["plan"],
        "calls_used": 0,
        "calls_limit": user["monthly_limit"],
        "calls_remaining": user["monthly_limit"],
        "created_at": user["created_at"].isoformat(),
        "message": "API key created successfully. You have 500 free calls."
    }


def create_key_file(email: str) -> dict:
    keys = load_keys()

    for key, data in keys.items():
        if data["email"].lower() == email.lower():
            return {
                "already_exists": True,
                "api_key": key,
                "email": email,
                "plan": data.get("plan", "Free"),
                "calls_used": data["calls_used"],
                "calls_limit": data["calls_limit"],
                "calls_remaining": data["calls_limit"] - data["calls_used"],
                "created_at": data["created_at"],
                "message": "You already have an API key."
            }

    api_key = generate_api_key()
    keys[api_key] = {
        "email": email.lower().strip(),
        "plan": "Free",
        "calls_used": 0,
        "calls_limit": MONTHLY_LIMIT,
        "created_at": iso_now(),
        "last_used": None,
        "active": True
    }
    save_keys(keys)

    return {
        "already_exists": False,
        "api_key": api_key,
        "email": email,
        "plan": "Free",
        "calls_used": 0,
        "calls_limit": MONTHLY_LIMIT,
        "calls_remaining": MONTHLY_LIMIT,
        "created_at": keys[api_key]["created_at"],
        "message": "API key created successfully. You have 500 free calls."
    }


def validate_key(api_key: str) -> dict:
    if not api_key:
        return {
            "valid": False,
            "reason": "missing",
            "message": "API key missing. Add X-API-Key header."
        }

    if use_postgres():
        return validate_key_db(api_key)
    return validate_key_file(api_key)


def validate_key_db(api_key: str) -> dict:
    start, end = current_month_bounds()
    api_key_hash = hash_key(api_key)

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, email, plan, monthly_limit, active
                from api_users
                where api_key_hash = %s
                """,
                (api_key_hash,),
            )
            user = cur.fetchone()

            if not user:
                return {
                    "valid": False,
                    "reason": "invalid",
                    "message": "Invalid API key. Get yours at medtechtools.io"
                }

            if not user["active"]:
                return {
                    "valid": False,
                    "reason": "disabled",
                    "message": "This API key has been disabled. Contact support."
                }

            cur.execute(
                """
                select count(*) as calls_used
                from api_usage
                where user_id = %s and created_at >= %s and created_at < %s
                """,
                (user["id"], start, end),
            )
            calls_used = cur.fetchone()["calls_used"]

    if calls_used >= user["monthly_limit"]:
        return {
            "valid": False,
            "reason": "limit_exceeded",
            "message": f"Monthly limit of {user['monthly_limit']} calls reached.",
            "user_id": str(user["id"]),
            "email": user["email"],
            "calls_used": calls_used,
            "calls_limit": user["monthly_limit"],
            "upgrade": "Contact us to increase your limit."
        }

    return {
        "valid": True,
        "user_id": str(user["id"]),
        "email": user["email"],
        "plan": user["plan"],
        "calls_used": calls_used,
        "calls_limit": user["monthly_limit"],
        "calls_remaining": user["monthly_limit"] - calls_used
    }


def validate_key_file(api_key: str) -> dict:
    keys = load_keys()

    if api_key not in keys:
        return {
            "valid": False,
            "reason": "invalid",
            "message": "Invalid API key. Get yours at medtechtools.io"
        }

    key_data = keys[api_key]
    if not key_data.get("active", True):
        return {
            "valid": False,
            "reason": "disabled",
            "message": "This API key has been disabled. Contact support."
        }

    calls_used = key_data["calls_used"]
    calls_limit = key_data["calls_limit"]

    if calls_used >= calls_limit:
        return {
            "valid": False,
            "reason": "limit_exceeded",
            "message": f"Monthly limit of {calls_limit} calls reached.",
            "email": key_data["email"],
            "calls_used": calls_used,
            "calls_limit": calls_limit,
            "upgrade": "Contact us to increase your limit."
        }

    return {
        "valid": True,
        "email": key_data["email"],
        "plan": key_data.get("plan", "Free"),
        "calls_used": calls_used,
        "calls_limit": calls_limit,
        "calls_remaining": calls_limit - calls_used
    }


def record_usage(api_key: str, endpoint: str, method: str, status_code: int, response_time_ms: int):
    if use_postgres():
        return record_usage_db(api_key, endpoint, method, status_code, response_time_ms)
    return record_usage_file(api_key, endpoint, method, status_code, response_time_ms)


def record_usage_db(api_key: str, endpoint: str, method: str, status_code: int, response_time_ms: int):
    api_key_hash = hash_key(api_key)
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("select id from api_users where api_key_hash = %s", (api_key_hash,))
            user = cur.fetchone()
            if not user:
                return

            cur.execute(
                """
                insert into api_usage (user_id, endpoint, method, status_code, response_time_ms)
                values (%s, %s, %s, %s, %s)
                """,
                (user["id"], endpoint, method, status_code, response_time_ms),
            )
            cur.execute("update api_users set last_used_at = now(), updated_at = now() where id = %s", (user["id"],))


def record_usage_file(api_key: str, endpoint: str, method: str, status_code: int, response_time_ms: int):
    keys = load_keys()
    if api_key in keys:
        keys[api_key]["calls_used"] += 1
        keys[api_key]["last_used"] = iso_now()
        save_keys(keys)

        os.makedirs(os.path.dirname(USAGE_PATH), exist_ok=True)
        with open(USAGE_PATH, "a") as f:
            f.write(json.dumps({
                "api_key": api_key,
                "email": keys[api_key]["email"],
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "created_at": iso_now(),
            }) + "\n")


def increment_usage(api_key: str):
    record_usage(api_key, "unknown", "UNKNOWN", 200, 0)


def get_usage(api_key: str) -> dict:
    if use_postgres():
        return get_usage_db(api_key)
    return get_usage_file(api_key)


def get_usage_db(api_key: str) -> dict:
    validation = validate_key_db(api_key)
    if not validation["valid"] and validation["reason"] != "limit_exceeded":
        return {"error": "Key not found"}

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select created_at, last_used_at, active
                from api_users
                where api_key_hash = %s
                """,
                (hash_key(api_key),),
            )
            user = cur.fetchone()

    return {
        "email": validation["email"],
        "plan": validation.get("plan", "Free"),
        "calls_used": validation["calls_used"],
        "calls_limit": validation["calls_limit"],
        "calls_remaining": max(0, validation["calls_limit"] - validation["calls_used"]),
        "created_at": user["created_at"].isoformat() if user and user["created_at"] else None,
        "last_used": user["last_used_at"].isoformat() if user and user["last_used_at"] else None,
        "active": user["active"] if user else False
    }


def get_usage_file(api_key: str) -> dict:
    keys = load_keys()
    if api_key not in keys:
        return {"error": "Key not found"}

    data = keys[api_key]
    return {
        "email": data["email"],
        "plan": data.get("plan", "Free"),
        "calls_used": data["calls_used"],
        "calls_limit": data["calls_limit"],
        "calls_remaining": data["calls_limit"] - data["calls_used"],
        "created_at": data["created_at"],
        "last_used": data["last_used"],
        "active": data["active"]
    }


def get_admin_metrics() -> dict:
    if use_postgres():
        return get_admin_metrics_db()
    return get_admin_metrics_file()


def get_admin_metrics_db() -> dict:
    start, end = current_month_bounds()
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) as count from api_users")
            total_users = cur.fetchone()["count"]

            cur.execute("select count(*) as count from api_usage")
            total_calls = cur.fetchone()["count"]

            cur.execute("select count(*) as count from api_usage where created_at >= now() - interval '1 day'")
            calls_today = cur.fetchone()["count"]

            cur.execute("select count(*) as count from api_usage where created_at >= now() - interval '7 days'")
            calls_7d = cur.fetchone()["count"]

            cur.execute("select count(distinct user_id) as count from api_usage where created_at >= now() - interval '7 days'")
            active_users_7d = cur.fetchone()["count"]

            cur.execute(
                """
                select endpoint, count(*) as calls
                from api_usage
                group by endpoint
                order by calls desc
                limit 10
                """
            )
            endpoint_usage = cur.fetchall()

            cur.execute(
                """
                select
                    u.email,
                    u.plan,
                    u.monthly_limit,
                    u.last_used_at,
                    count(a.id) filter (where a.created_at >= %s and a.created_at < %s) as calls_used
                from api_users u
                left join api_usage a on a.user_id = u.id
                group by u.id
                order by calls_used desc, u.created_at desc
                limit 20
                """,
                (start, end),
            )
            top_users = cur.fetchall()

            cur.execute(
                """
                select
                    round(100.0 * count(*) filter (where status_code >= 400) / nullif(count(*), 0), 2) as error_rate,
                    round(avg(response_time_ms), 0) as avg_response_time_ms
                from api_usage
                """
            )
            health = cur.fetchone()

    return {
        "storage": "supabase_postgres",
        "total_users": total_users,
        "total_api_keys": total_users,
        "total_calls": total_calls,
        "calls_today": calls_today,
        "calls_7d": calls_7d,
        "active_users_7d": active_users_7d,
        "error_rate": float(health["error_rate"] or 0),
        "avg_response_time_ms": int(health["avg_response_time_ms"] or 0),
        "endpoint_usage": endpoint_usage,
        "top_users": [
            {
                "email": row["email"],
                "plan": row["plan"],
                "calls_used": row["calls_used"],
                "monthly_limit": row["monthly_limit"],
                "last_used_at": row["last_used_at"].isoformat() if row["last_used_at"] else None,
            }
            for row in top_users
        ],
    }


def get_admin_metrics_file() -> dict:
    keys = load_keys()
    usage_rows = []
    if os.path.exists(USAGE_PATH):
        with open(USAGE_PATH, "r") as f:
            usage_rows = [json.loads(line) for line in f if line.strip()]

    endpoint_counts = {}
    for row in usage_rows:
        endpoint = row.get("endpoint", "unknown")
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

    total_calls = len(usage_rows) or sum(data.get("calls_used", 0) for data in keys.values())
    error_count = sum(1 for row in usage_rows if row.get("status_code", 200) >= 400)
    avg_ms = 0
    if usage_rows:
        avg_ms = int(sum(row.get("response_time_ms", 0) for row in usage_rows) / len(usage_rows))

    return {
        "storage": "local_file_fallback",
        "total_users": len(keys),
        "total_api_keys": len(keys),
        "total_calls": total_calls,
        "calls_today": total_calls,
        "calls_7d": total_calls,
        "active_users_7d": len([data for data in keys.values() if data.get("last_used")]),
        "error_rate": round((error_count / len(usage_rows)) * 100, 2) if usage_rows else 0,
        "avg_response_time_ms": avg_ms,
        "endpoint_usage": [
            {"endpoint": endpoint, "calls": calls}
            for endpoint, calls in sorted(endpoint_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "top_users": [
            {
                "email": data["email"],
                "plan": data.get("plan", "Free"),
                "calls_used": data.get("calls_used", 0),
                "monthly_limit": data.get("calls_limit", MONTHLY_LIMIT),
                "last_used_at": data.get("last_used"),
            }
            for data in sorted(keys.values(), key=lambda item: item.get("calls_used", 0), reverse=True)
        ],
    }


def delete_user(email: str) -> dict:
    if use_postgres():
        return delete_user_db(email)
    return delete_user_file(email)


def delete_user_db(email: str) -> dict:
    clean_email = email.lower().strip()
    
    with db_connect() as conn:
        with conn.cursor() as cur:
            # First get the user_id
            cur.execute("SELECT id FROM api_users WHERE email = %s", (clean_email,))
            user = cur.fetchone()
            
            if not user:
                return {"success": False, "message": "User not found"}
            
            user_id = user["id"]
            
            # Delete user's API usage records
            cur.execute("DELETE FROM api_usage WHERE user_id = %s", (user_id,))
            
            # Delete the user (this cascades to api_keys)
            cur.execute("DELETE FROM api_users WHERE id = %s", (user_id,))
            
            conn.commit()
    
    return {"success": True, "message": f"User {email} deleted successfully"}


def delete_user_file(email: str) -> dict:
    clean_email = email.lower().strip()
    keys = load_keys()
    
    # Find the API key for this email
    api_key_to_delete = None
    for api_key, data in keys.items():
        if data.get("email", "").lower() == clean_email:
            api_key_to_delete = api_key
            break
    
    if not api_key_to_delete:
        return {"success": False, "message": "User not found"}
    
    # Remove the user from keys
    del keys[api_key_to_delete]
    save_keys(keys)
    
    return {"success": True, "message": f"User {email} deleted successfully"}
