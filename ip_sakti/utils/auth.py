"""
ip_sakti.utils.auth — Authentication & User Security Service.

Implements user registration, credential verification, and session management
backed by Supabase Auth (auth.users & public.profiles).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from ip_sakti.utils.supabase_auth import SupabaseAuthService

import hashlib
import secrets

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with random salt."""
    salt = secrets.token_hex(16)
    iterations = 100000
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${key.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against PBKDF2 hash string."""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = parts[2]
        key = parts[3]
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
        return secrets.compare_digest(new_key.hex(), key)
    except Exception:
        return False


class AuthService:
    """
    Manages user authentication and profile persistence in Supabase Auth & PostgreSQL.
    Supports local SQLite fallback for testing environments when db_manager is passed.
    """

    def __init__(self, db_manager: Any = None) -> None:
        """Initialise AuthService backed by SupabaseAuthService with local DB fallback."""
        self.db_manager = db_manager
        self.supabase_auth = SupabaseAuthService()

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        confirm_password: str,
        terms_accepted: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Register a new user via Supabase Auth or local SQLite fallback.
        """
        if password != confirm_password:
            return None, "Passwords do not match."

        # ── SQLite-only mode (Supabase not configured, local DB manager present) ──
        if self.db_manager and not self.supabase_auth.is_supabase_enabled:
            if not name or not name.strip():
                return None, "Full Name is required."
            import re as _re
            email_pattern = _re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
            if not email or not email.strip() or not email_pattern.match(email.strip()):
                return None, "Please enter a valid email address."
            if not password or len(password) < 6:
                return None, "Password must be at least 6 characters long."
            if password != confirm_password:
                return None, "Passwords do not match."
            if not terms_accepted:
                return None, "Please accept the Terms of Service and Privacy Policy."

            try:
                import uuid
                from datetime import datetime, timezone
                user_id = str(uuid.uuid4())
                pw_hash = hash_password(password)
                created_at = datetime.now(timezone.utc).isoformat()
                clean_name = name.strip()
                clean_email = email.strip().lower()
                conn = self.db_manager.connection
                with conn:
                    cur = conn.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
                    if cur.fetchone():
                        return None, "An account with this email already exists."
                    conn.execute(
                        "INSERT INTO users (id, email, password_hash, full_name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_id, clean_email, pw_hash, clean_name, "innovator", created_at),
                    )
                user_dict = {
                    "id": user_id,
                    "email": clean_email,
                    "name": clean_name,
                    "created_at": created_at,
                }
                return user_dict, None
            except Exception as exc:
                logger.warning(f"Local SQLite user registration failed: {exc}")
                return None, f"Registration failed: {exc}"

        user, err = self.supabase_auth.register_user(
            name=name,
            email=email,
            password=password,
            confirm_password=confirm_password,
            terms_accepted=terms_accepted,
        )
        if user:
            return user, None

        return None, err or "Registration failed."

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate a user by email and password.

        Tries Supabase first; falls back to local SQLite when Supabase
        is not configured or the user only exists in the local database.
        """
        # ── SQLite-only mode (Supabase not configured) ────────────────────────
        if self.db_manager and not self.supabase_auth.is_supabase_enabled:
            try:
                conn = self.db_manager.connection
                cur = conn.execute(
                    "SELECT id, email, password_hash, full_name, created_at FROM users WHERE email = ?",
                    (email.lower().strip(),)
                )
                row = cur.fetchone()
                if row and verify_password(password, row["password_hash"]):
                    user_dict = {
                        "id": row["id"],
                        "email": row["email"],
                        "name": row["full_name"],
                        "created_at": row["created_at"],
                    }
                    return user_dict, None
                return None, "Incorrect email or password."
            except Exception as exc:
                logger.warning(f"Local SQLite authentication failed: {exc}")
            return None, "Incorrect email or password."

        # ── Supabase path ─────────────────────────────────────────────────────
        user, err = self.supabase_auth.authenticate_user(email=email, password=password)
        if user:
            return user, None

        # ── SQLite fallback when Supabase fails and local db exists ───────────
        if self.db_manager:
            try:
                conn = self.db_manager.connection
                cur = conn.execute(
                    "SELECT id, email, password_hash, full_name, created_at FROM users WHERE email = ?",
                    (email.lower().strip(),)
                )
                row = cur.fetchone()
                if row and verify_password(password, row["password_hash"]):
                    user_dict = {
                        "id": row["id"],
                        "email": row["email"],
                        "name": row["full_name"],
                        "created_at": row["created_at"],
                    }
                    return user_dict, None
                return None, "Incorrect email or password."
            except Exception as exc:
                logger.warning(f"Local SQLite authentication failed: {exc}")

        return None, err or "Incorrect email or password."

    def verify_session(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify an authenticated session token via Supabase Auth.
        """
        return self.supabase_auth.verify_session(access_token)

    def update_profile(
        self,
        access_token: str,
        profile_data: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Update user profile across Supabase Auth metadata and profiles table.
        """
        return self.supabase_auth.update_profile(access_token, profile_data)

    def send_magic_link(
        self,
        email: str,
        redirect_to: str = "http://localhost:3000/auth/callback",
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a Magic Link OTP email via Supabase Auth for passwordless sign-in.
        """
        return self.supabase_auth.send_magic_link(email=email, redirect_to=redirect_to)

    def sign_out(self, access_token: Optional[str] = None) -> bool:
        """
        Sign out session from Supabase Auth.
        """
        return self.supabase_auth.sign_out(access_token)


