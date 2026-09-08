"""
ip_sakti.utils.supabase_auth — Persistent Supabase Authentication Adapter.

Provides seamless integration with Supabase Auth (GoTrue) while maintaining
full interface compatibility with the existing SQLite-backed AuthService.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional, Tuple

from ip_sakti.utils.auth import AuthService as SQLiteAuthService
from ip_sakti.utils.db import DatabaseManager
from ip_sakti.utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SupabaseAuthService:
    """
    Manages user authentication via Supabase Auth with automatic SQLite fallback.
    """

    def __init__(
        self,
        supabase_client: Optional[SupabaseClient] = None,
        fallback_service: Optional[SQLiteAuthService] = None,
    ) -> None:
        self.client = supabase_client or SupabaseClient()
        self.fallback = fallback_service or SQLiteAuthService(db_manager=DatabaseManager())

    @property
    def is_supabase_enabled(self) -> bool:
        """Check if Supabase Auth is enabled and configured."""
        return self.client.is_configured

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        confirm_password: str,
        terms_accepted: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Register a new user via Supabase Auth (or SQLite fallback).
        """
        # Common preliminary validations
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

        if not self.is_supabase_enabled:
            return self.fallback.register_user(
                name=clean_name,
                email=clean_email,
                password=password,
                confirm_password=confirm_password,
                terms_accepted=terms_accepted,
            )

        try:
            res = self.client.sign_up(
                email=clean_email,
                password=password,
                user_metadata={"display_name": clean_name, "name": clean_name},
            )
            user_data = res.get("user") or res
            user_id = user_data.get("id")

            # Insert into public.profiles table if user_id is returned
            if user_id:
                try:
                    self.client.insert(
                        table="profiles",
                        data={"id": user_id, "display_name": clean_name, "preferred_language": "en"},
                        token=res.get("access_token"),
                        use_service_role=True if self.client.service_role_key else False,
                    )
                except Exception as p_exc:
                    logger.warning(f"Could not auto-create profile in Supabase: {p_exc}")

            return {
                "id": user_id,
                "name": clean_name,
                "email": clean_email,
                "access_token": res.get("access_token"),
                "refresh_token": res.get("refresh_token"),
            }, None

        except ValueError as val_err:
            return None, str(val_err)
        except Exception as exc:
            logger.error(f"Supabase user registration error: {exc}")
            # Fallback to local SQLite if Supabase service failed
            logger.info("Falling back to local SQLite registration due to Supabase error.")
            return self.fallback.register_user(
                name=clean_name,
                email=clean_email,
                password=password,
                confirm_password=confirm_password,
                terms_accepted=terms_accepted,
            )

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user credentials against Supabase Auth (or SQLite fallback).
        """
        if not email or not email.strip() or not password:
            return None, "Incorrect email or password."

        clean_email = email.strip().lower()

        if not self.is_supabase_enabled:
            return self.fallback.authenticate_user(clean_email, password)

        try:
            res = self.client.sign_in_with_password(clean_email, password)
            user_obj = res.get("user", {})
            user_meta = user_obj.get("user_metadata", {})
            user_name = user_meta.get("display_name") or user_meta.get("name") or clean_email.split("@")[0]
            user_id = user_obj.get("id")

            # Synchronize user into local SQLite users table to allow foreign keys in user_sessions & conversations
            if user_id and hasattr(self.fallback, "db"):
                try:
                    from datetime import datetime, timezone
                    conn = self.fallback.db.connection
                    now_iso = datetime.now(timezone.utc).isoformat()
                    with conn:
                        conn.execute(
                            """
                            INSERT INTO users (id, name, email, password_hash, created_at)
                            VALUES (?, ?, ?, 'supabase_auth', ?)
                            ON CONFLICT(id) DO UPDATE SET name=excluded.name, email=excluded.email
                            """,
                            (user_id, user_name, clean_email, now_iso),
                        )
                except Exception as sync_exc:
                    logger.warning(f"Could not sync Supabase user locally: {sync_exc}")

            return {
                "id": user_id,
                "name": user_name,
                "email": clean_email,
                "access_token": res.get("access_token"),
                "refresh_token": res.get("refresh_token"),
            }, None

        except ValueError as val_err:
            return None, str(val_err)
        except Exception as exc:
            logger.error(f"Supabase authentication error: {exc}")
            # Fallback to local SQLite if Supabase service failed
            logger.info("Falling back to local SQLite authentication due to Supabase error.")
            return self.fallback.authenticate_user(clean_email, password)

    def verify_session(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify persistent session via access token.
        """
        if not access_token:
            return None
        if not self.is_supabase_enabled:
            return None

        try:
            user_obj = self.client.get_user(access_token)
            if not user_obj:
                return None
            user_meta = user_obj.get("user_metadata", {})
            user_name = user_meta.get("display_name") or user_meta.get("name") or user_obj.get("email", "").split("@")[0]
            return {
                "id": user_obj.get("id"),
                "name": user_name,
                "email": user_obj.get("email"),
                "access_token": access_token,
            }
        except Exception as exc:
            logger.warning(f"Session token verification error: {exc}")
            return None

    def sign_out(self, access_token: Optional[str] = None) -> bool:
        """
        Terminate session in Supabase Auth.
        """
        if not access_token or not self.is_supabase_enabled:
            return True
        return self.client.sign_out(access_token)
