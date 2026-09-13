"""
ip_sakti.utils.supabase_auth — Persistent Supabase Authentication Adapter.

Provides seamless integration with Supabase Auth (GoTrue).
All persistence is backed by Supabase PostgreSQL (auth.users & public.profiles).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from ip_sakti.utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SupabaseAuthService:
    """
    Manages user authentication via Supabase Auth.
    """

    def __init__(
        self,
        supabase_client: Optional[SupabaseClient] = None,
    ) -> None:
        self.client = supabase_client or SupabaseClient()
        self._mem_users: Dict[str, Dict[str, Any]] = {}

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
        Register a new user via Supabase Auth.
        """
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
            # Memory store for unconfigured local mode
            if clean_email in self._mem_users:
                return None, "An account with this email already exists."
            user_id = f"usr-{uuid4()}"
            now_iso = datetime.now(timezone.utc).isoformat()
            user_rec = {
                "id": user_id,
                "name": clean_name,
                "email": clean_email,
                "created_at": now_iso,
                "password": password,  # store for in-memory auth only (never persisted)
            }
            self._mem_users[clean_email] = user_rec
            return {k: v for k, v in user_rec.items() if k != "password"}, None

        try:
            if self.client.service_role_key:
                # Use Admin API: creates real user in auth.users, avoids SMTP delivery failure
                res = self.client.admin_create_user(
                    email=clean_email,
                    password=password,
                    user_metadata={"name": clean_name, "display_name": clean_name, "fullName": clean_name},
                    email_confirm=True,
                )
                user_id = res.get("id")
            else:
                res = self.client.sign_up(
                    email=clean_email,
                    password=password,
                    user_metadata={"display_name": clean_name, "name": clean_name, "fullName": clean_name},
                )
                user_data = res.get("user") or res
                user_id = user_data.get("id")

            if not user_id:
                return None, "Supabase failed to create a valid user record."

            # Insert profile in public.profiles with the same UUID
            try:
                self.client.insert(
                    table="profiles",
                    data={"id": user_id, "display_name": clean_name, "preferred_language": "en"},
                    use_service_role=True if self.client.service_role_key else False,
                )
            except Exception as p_exc:
                logger.warning(f"Could not auto-create profile in Supabase: {p_exc}")

            # Sign in with password to obtain immediate live access token
            token = res.get("access_token")
            refresh_token = res.get("refresh_token")
            if not token:
                try:
                    signin_res = self.client.sign_in_with_password(clean_email, password)
                    token = signin_res.get("access_token")
                    refresh_token = signin_res.get("refresh_token")
                except Exception as signin_exc:
                    logger.warning(f"Auto-signin after registration: {signin_exc}")

            reg_rec = {
                "id": user_id,
                "name": clean_name,
                "email": clean_email,
                "access_token": token,
                "refresh_token": refresh_token,
            }
            self._mem_users[clean_email] = reg_rec
            return reg_rec, None

        except (ValueError, Exception) as exc:
            logger.warning(f"Supabase user registration error: {exc}")
            exc_str = str(exc).lower()

            if "already registered" in exc_str or "already been registered" in exc_str or "email_exists" in exc_str or "already exists" in exc_str or "422" in exc_str:
                return None, "An account with this email already exists. Please login."

            return None, str(exc)

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user credentials against Supabase Auth.
        """
        if not email or not email.strip() or not password:
            return None, "Incorrect email or password."

        clean_email = email.strip().lower()

        if not self.is_supabase_enabled:
            # Memory-store authentication for unit tests / offline mode.
            user_rec = self._mem_users.get(clean_email)
            if user_rec and user_rec.get("password") == password:
                return {k: v for k, v in user_rec.items() if k != "password"}, None
            return None, "Incorrect email or password."

        try:
            res = self.client.sign_in_with_password(clean_email, password)
            user_obj = res.get("user", {})
            user_meta = user_obj.get("user_metadata", {})
            user_id = user_obj.get("id")
            access_token = res.get("access_token")

            if not access_token or not user_id:
                return None, "Supabase authentication returned invalid session payload."

            # Fetch profile display name if available
            display_name = user_meta.get("display_name") or user_meta.get("fullName") or user_meta.get("name")
            try:
                prof_rows = self.client.select(
                    table="profiles",
                    params={"id": f"eq.{user_id}", "select": "*"},
                    token=access_token,
                )
                if prof_rows and prof_rows[0].get("display_name"):
                    display_name = prof_rows[0].get("display_name")
            except Exception:
                pass

            user_name = display_name or clean_email.split("@")[0]

            return {
                "id": user_id,
                "name": user_name,
                "email": clean_email,
                "access_token": access_token,
                "refresh_token": res.get("refresh_token"),
                "organization": user_meta.get("organization", "IP-SAKTI"),
                "role": user_meta.get("role", "Researcher"),
                "bio": user_meta.get("bio", ""),
                "avatarUrl": user_meta.get("avatarUrl", ""),
                "user_metadata": user_meta,
            }, None

        except (ValueError, Exception) as exc:
            logger.error(f"Supabase authentication error for {clean_email}: {exc}")
            err_msg = str(exc)
            if "invalid login credentials" in err_msg.lower() or "400" in err_msg:
                return None, "Invalid login credentials"
            return None, f"Authentication failed: {exc}"

    def verify_session(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify persistent session via access token and hydrate user/profile state.
        """
        if not access_token or not self.is_supabase_enabled:
            return None

        try:
            user_obj = self.client.get_user(access_token)
            if not user_obj or "id" not in user_obj:
                return None
            user_id = user_obj.get("id")
            user_meta = user_obj.get("user_metadata", {})

            # Attempt to read latest display name from public.profiles
            profile_display_name = None
            try:
                prof_rows = self.client.select(
                    table="profiles",
                    params={"id": f"eq.{user_id}", "select": "*"},
                    token=access_token,
                )
                if prof_rows and prof_rows[0].get("display_name"):
                    profile_display_name = prof_rows[0].get("display_name")
            except Exception:
                pass

            user_name = profile_display_name or user_meta.get("display_name") or user_meta.get("fullName") or user_meta.get("name") or user_obj.get("email", "").split("@")[0]
            return {
                "id": user_id,
                "name": user_name,
                "email": user_obj.get("email"),
                "access_token": access_token,
                "organization": user_meta.get("organization", "IP-SAKTI"),
                "role": user_meta.get("role", "Researcher"),
                "bio": user_meta.get("bio", ""),
                "avatarUrl": user_meta.get("avatarUrl", ""),
                "user_metadata": user_meta,
            }
        except Exception as exc:
            logger.warning(f"Session token verification error: {exc}")
            return None

    def update_profile(
        self,
        access_token: str,
        profile_data: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Update user profile in Supabase Auth metadata and public.profiles table.
        """
        if not access_token or not self.is_supabase_enabled:
            return None, "Authentication service not configured."

        verified = self.verify_session(access_token)
        if not verified:
            return None, "Invalid or expired session token."

        user_id = verified["id"]
        full_name = profile_data.get("fullName") or profile_data.get("name") or verified.get("name")

        meta_update = {
            "fullName": full_name,
            "display_name": full_name,
            "organization": profile_data.get("organization", verified.get("organization", "IP-SAKTI")),
            "role": profile_data.get("role", verified.get("role", "Researcher")),
            "bio": profile_data.get("bio", verified.get("bio", "")),
            "avatarUrl": profile_data.get("avatarUrl", verified.get("avatarUrl", "")),
        }

        try:
            # 1. Update GoTrue user metadata
            self.client.update_user_metadata(access_token, meta_update)

            # 2. Update public.profiles row
            try:
                self.client.update(
                    table="profiles",
                    data={"display_name": full_name},
                    params={"id": f"eq.{user_id}"},
                    token=access_token,
                )
            except Exception as p_err:
                logger.warning(f"Updating public.profiles for {user_id}: {p_err}")

            return {
                "id": user_id,
                "fullName": full_name,
                "email": verified.get("email"),
                "organization": meta_update["organization"],
                "role": meta_update["role"],
                "bio": meta_update["bio"],
                "avatarUrl": meta_update["avatarUrl"],
            }, None
        except Exception as exc:
            logger.error(f"Error updating profile for {user_id}: {exc}")
            return None, f"Failed to update profile: {exc}"

    def send_magic_link(
        self,
        email: str,
        redirect_to: str = "http://localhost:3000/auth/callback",
    ) -> Tuple[bool, Optional[str]]:
        """
        Trigger a Supabase Magic Link email for passwordless sign-in.
        Strictly enforces that unregistered emails CANNOT create accounts or receive magic links.
        """
        if not email or not email.strip() or not _EMAIL_REGEX.match(email.strip()):
            return False, "Please enter a valid email address."

        if not self.is_supabase_enabled:
            return False, "Authentication service is not configured."

        clean_email = email.strip().lower()
        try:
            self.client.sign_in_with_otp(
                email=clean_email,
                redirect_to=redirect_to,
                should_create_user=False,
            )
            return True, None
        except (ValueError, Exception) as exc:
            logger.error(f"Magic link send failed for {clean_email}: {exc}")
            exc_str = str(exc).lower()
            if "otp_disabled" in exc_str or "signups not allowed" in exc_str or "422" in exc_str:
                return False, "No account found with this email address. Please register first."
            if "403" in exc_str or "testing emails" in exc_str:
                return (
                    False,
                    "Email delivery restricted by test domain to the account owner. "
                    "Please use password login or contact the administrator.",
                )
            if "500" in exc_str or "error sending" in exc_str:
                return (
                    False,
                    "Email delivery failed (SMTP provider restriction). Please use your password to log in.",
                )
            return False, f"Failed to send magic link: {exc}"

    def sign_out(self, access_token: Optional[str] = None) -> bool:
        """
        Terminate session in Supabase Auth.
        """
        if not access_token or not self.is_supabase_enabled:
            return True
        return self.client.sign_out(access_token)


