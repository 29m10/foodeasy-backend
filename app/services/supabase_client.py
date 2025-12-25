from supabase import create_client, Client
from dotenv import load_dotenv
import os
from typing import Optional

# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validate required environment variables
if not SUPABASE_URL or SUPABASE_URL.strip() == "":
    raise ValueError(
        "SUPABASE_URL environment variable is not set or is empty. "
        "Please check your .env file or environment variables."
    )
if not SUPABASE_KEY or SUPABASE_KEY.strip() == "":
    raise ValueError(
        "SUPABASE_KEY environment variable is not set or is empty. "
        "Please check your .env file or environment variables."
    )
if not SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_ROLE_KEY.strip() == "":
    raise ValueError(
        "SUPABASE_SERVICE_ROLE_KEY environment variable is not set or is empty. "
        "Please check your .env file or environment variables."
    )

# Validate URL format
if not SUPABASE_URL.startswith(("http://", "https://")):
    raise ValueError(
        f"SUPABASE_URL must start with http:// or https://. "
        f"Current value: {SUPABASE_URL[:50]}..." if len(SUPABASE_URL) > 50 else f"Current value: {SUPABASE_URL}"
    )

# Create clients
supabase: Optional[Client] = None
supabase_admin: Optional[Client] = None

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
except Exception as e:
    error_msg = str(e)
    if "nodename nor servname provided" in error_msg or "not known" in error_msg:
        raise RuntimeError(
            f"Failed to connect to Supabase: DNS resolution error. "
            f"This usually means SUPABASE_URL is incorrect or not set properly. "
            f"URL format should be: https://your-project-id.supabase.co "
            f"Current URL: {SUPABASE_URL[:50]}..." if len(SUPABASE_URL) > 50 else f"Current URL: {SUPABASE_URL}"
        ) from e
    raise RuntimeError(f"Failed to create Supabase clients: {error_msg}") from e


def get_supabase_client() -> Client:
    """
    Get regular Supabase client (respects Row Level Security - RLS).
    
    This client uses the anon/public key and respects RLS policies.
    Use this for client-side operations where you want security policies enforced.
    
    Returns:
        Client: Supabase client instance with RLS enabled
    """
    if supabase is None:
        raise RuntimeError("Supabase client not initialized")
    return supabase


def get_supabase_admin() -> Client:
    """
    Get admin Supabase client (bypasses Row Level Security - RLS).
    
    This client uses the service role key and bypasses all RLS policies.
    Use this for server-side operations that need full database access.
    WARNING: Only use this in secure server environments, never expose to clients.
    
    Returns:
        Client: Supabase admin client instance with RLS bypassed
    """
    if supabase_admin is None:
        raise RuntimeError("Supabase admin client not initialized")
    return supabase_admin