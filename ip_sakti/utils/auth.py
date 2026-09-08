"""
ip_sakti.utils.auth — Authentication & User Security Service.

Implements PBKDF2-SHA256 password hashing (Python stdlib), user registration,
credential verification, and user management using SQLite persistence.
"""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from ip_sakti.utils.db import DatabaseManager

logger = logging.getLogger(__name__)

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random salt.

    Returns string in format: salt_hex$hash_hex
    """
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt,
        iterations=100_000,
    )
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a stored PBKDF2 salt$hash string.
    """
    try:
        parts = password_hash.split("$")
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        expected_key = bytes.fromhex(parts[1])
        key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=100_000,
        )
        return secrets.compare_digest(key, expected_key)
    except Exception as exc:
        logger.warning(f"Password verification error: {exc}")
        return False


import os

class AuthService:
    """
    Manages user authentication and user record persistence in Supabase (production)
    or SQLite (local/testing fallback).
    """

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        """Initialise AuthService with optional DatabaseManager or Supabase backend."""
        self.db = db_manager or DatabaseManager()
        self.supabase_auth = None
        if db_manager is None and os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
            try:
                from ip_sakti.utils.supabase_auth import SupabaseAuthService
                self.supabase_auth = SupabaseAuthService()
                logger.info("AuthService using persistent Supabase Auth backend.")
            except Exception as exc:
                logger.warning(f"Could not initialise SupabaseAuthService: {exc}. Using SQLite.")

        try:
            self.db.initialise()
        except Exception as exc:
            logger.warning(f"Failed to initialise database in AuthService: {exc}")

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        confirm_password: str,
        terms_accepted: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Register a new user.

        Returns (user_dict, error_message).
        """
        if self.supabase_auth is not None:
            return self.supabase_auth.register_user(
                name=name,
                email=email,
                password=password,
                confirm_password=confirm_password,
                terms_accepted=terms_accepted,
            )
        # 1. Validation checks
        if not name or not name.strip():
            return None, "Full Name is required."
        if not email or not email.strip() or not _EMAIL_REGEX.match(email.strip()):
            return None, "Please enter a valid email address."
        if not password or len(password) < 6:
            return None, "Password must be at least 6 characters long."
        if password != confirm_password:
            return None, "Passwords do not match."
        if not terms_accepted:
            return None, "Please accept the Terms of Service and Privacy Policy."

        clean_name = name.strip()
        clean_email = email.strip().lower()
        user_id = str(uuid4())
        pwd_hash = hash_password(password)
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            conn = self.db.connection
            with conn:
                # Duplicate email check
                existing = conn.execute(
                    "SELECT id FROM users WHERE email = ?", (clean_email,)
                ).fetchone()
                if existing:
                    return None, "An account with this email already exists."

                conn.execute(
                    """
                    INSERT INTO users (id, name, email, password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, clean_name, clean_email, pwd_hash, now_iso),
                )
            logger.info("Registered new user", extra={"user_id": user_id, "email": clean_email})

            user_data = {
                "id": user_id,
                "name": clean_name,
                "email": clean_email,
                "created_at": now_iso,
            }
            return user_data, None
        except Exception as exc:
            logger.error(f"Failed to register user: {exc}")
            return None, "Database error during registration. Please try again."

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate a user by email and password.

        Returns (user_dict, error_message).
        """
        if self.supabase_auth is not None:
            return self.supabase_auth.authenticate_user(email=email, password=password)

        if not email or not email.strip() or not password:
            return None, "Incorrect email or password."

        clean_email = email.strip().lower()

        try:
            conn = self.db.connection
            row = conn.execute(
                "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
                (clean_email,),
            ).fetchone()

            if not row:
                return None, "Incorrect email or password."

            if not verify_password(password, row["password_hash"]):
                return None, "Incorrect email or password."

            user_data = {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "created_at": row["created_at"],
            }
            logger.info("Successfully authenticated user", extra={"user_id": row["id"]})
            return user_data, None
        except Exception as exc:
            logger.error(f"Error authenticating user {clean_email}: {exc}")
            return None, "An error occurred during authentication."

    def verify_session(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify an authenticated session token via Supabase Auth.
        """
        if self.supabase_auth is not None:
            return self.supabase_auth.verify_session(access_token)
        return None
