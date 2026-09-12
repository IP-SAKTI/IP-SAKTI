"""
ip_sakti.utils.supabase_client — Clean HTTP client wrapper for Supabase Auth & PostgREST.

Operates directly over Supabase REST APIs using httpx without hard dependencies
on proprietary binary drivers, supporting both authenticated user JWTs and anon access.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    HTTP client interface for Supabase Auth and PostgREST REST APIs.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_anon_key: Optional[str] = None,
        supabase_service_role_key: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        self.url = (supabase_url or os.getenv("SUPABASE_URL", "")).rstrip("/")
        self.anon_key = supabase_anon_key or os.getenv("SUPABASE_ANON_KEY", "")
        self.service_role_key = supabase_service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Check whether Supabase URL and anon key are properly configured."""
        return bool(self.url and self.anon_key)

    def _get_headers(self, token: Optional[str] = None, use_service_role: bool = False) -> Dict[str, str]:
        """Construct standard Supabase HTTP headers."""
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        if use_service_role and self.service_role_key:
            headers["apikey"] = self.service_role_key
            headers["Authorization"] = f"Bearer {self.service_role_key}"
        elif token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            headers["Authorization"] = f"Bearer {self.anon_key}"
        return headers

    # -------------------------------------------------------------------------
    # Authentication (GoTrue / Auth v1)
    # -------------------------------------------------------------------------

    def sign_up(self, email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a new user via Supabase Auth.
        """
        if not self.is_configured:
            raise RuntimeError("Supabase credentials not configured.")

        url = f"{self.url}/auth/v1/signup"
        payload: Dict[str, Any] = {"email": email, "password": password}
        if user_metadata:
            payload["data"] = user_metadata

        headers = self._get_headers()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                err_detail = resp.json().get("msg") or resp.json().get("error_description") or resp.text
                raise ValueError(f"Supabase signup failed ({resp.status_code}): {err_detail}")
            return resp.json()

    def sign_in_with_password(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with email and password via Supabase Auth.
        """
        if not self.is_configured:
            raise RuntimeError("Supabase credentials not configured.")

        url = f"{self.url}/auth/v1/token?grant_type=password"
        payload = {"email": email, "password": password}
        headers = self._get_headers()

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                err_detail = resp.json().get("msg") or resp.json().get("error_description") or resp.text
                raise ValueError(f"Supabase signin failed ({resp.status_code}): {err_detail}")
            return resp.json()

    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user details using their session access token.
        """
        if not self.is_configured:
            return None

        url = f"{self.url}/auth/v1/user"
        headers = self._get_headers(token=access_token)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                return None
        except Exception as exc:
            logger.warning(f"Error validating Supabase session token: {exc}")
            return None

    def sign_out(self, access_token: str) -> bool:
        """
        Sign out and invalidate session token.
        """
        if not self.is_configured:
            return True

        url = f"{self.url}/auth/v1/logout"
        headers = self._get_headers(token=access_token)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers)
                return resp.status_code in (200, 204)
        except Exception as exc:
            logger.warning(f"Error signing out from Supabase: {exc}")
            return False

    def sign_in_with_otp(self, email: str, redirect_to: str = "http://localhost:3000/auth/callback") -> bool:
        """
        Send a Magic Link OTP email to the user via Supabase Auth.

        Supabase will email the user a one-time link.  When the user clicks it,
        they are redirected to ``redirect_to`` with ``#access_token=...&type=magiclink``
        appended to the URL hash by the Supabase GoTrue server.

        Args:
            email: Destination email address.
            redirect_to: Frontend callback URL that will receive the session tokens.

        Returns:
            True if the email was dispatched successfully, False otherwise.

        Raises:
            RuntimeError: If Supabase credentials are not configured.
        """
        if not self.is_configured:
            raise RuntimeError("Supabase credentials not configured.")

        url = f"{self.url}/auth/v1/otp"
        payload: Dict[str, Any] = {
            "email": email,
            "create_user": False,
        }
        headers = self._get_headers()
        # Supabase reads redirect_to from query parameter, not body
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                url,
                json=payload,
                headers=headers,
                params={"redirect_to": redirect_to},
            )
            if resp.status_code >= 400:
                err_detail = resp.json().get("msg") or resp.json().get("error_description") or resp.text
                raise ValueError(f"Supabase magic link failed ({resp.status_code}): {err_detail}")
            return True

    # -------------------------------------------------------------------------
    # Database Operations (PostgREST /rest/v1)
    # -------------------------------------------------------------------------

    def insert(
        self,
        table: str,
        data: Dict[str, Any] | List[Dict[str, Any]],
        token: Optional[str] = None,
        use_service_role: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Insert record(s) into a PostgREST table.
        """
        if not self.is_configured:
            raise RuntimeError("Supabase credentials not configured.")

        url = f"{self.url}/rest/v1/{table}"
        headers = self._get_headers(token=token, use_service_role=use_service_role)

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=data, headers=headers)
            if resp.status_code >= 400:
                raise RuntimeError(f"Insert failed into {table} ({resp.status_code}): {resp.text}")
            return resp.json() if resp.text else []

    def select(
        self,
        table: str,
        params: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
        use_service_role: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Query records from a PostgREST table.
        """
        if not self.is_configured:
            raise RuntimeError("Supabase credentials not configured.")

        url = f"{self.url}/rest/v1/{table}"
        headers = self._get_headers(token=token, use_service_role=use_service_role)

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code >= 400:
                raise RuntimeError(f"Select failed from {table} ({resp.status_code}): {resp.text}")
            return resp.json() if resp.text else []

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        params: Dict[str, Any],
        token: Optional[str] = None,
        use_service_role: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Update records in a PostgREST table.
        """
        if not self.is_configured:
            raise RuntimeError("Supabase credentials not configured.")

        url = f"{self.url}/rest/v1/{table}"
        headers = self._get_headers(token=token, use_service_role=use_service_role)

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.patch(url, json=data, params=params, headers=headers)
            if resp.status_code >= 400:
                raise RuntimeError(f"Update failed on {table} ({resp.status_code}): {resp.text}")
            return resp.json() if resp.text else []

    def delete(
        self,
        table: str,
        params: Dict[str, Any],
        token: Optional[str] = None,
        use_service_role: bool = False,
    ) -> bool:
        """
        Delete records from a PostgREST table.
        """
        if not self.is_configured:
            raise RuntimeError("Supabase credentials not configured.")

        url = f"{self.url}/rest/v1/{table}"
        headers = self._get_headers(token=token, use_service_role=use_service_role)

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.delete(url, params=params, headers=headers)
            return resp.status_code in (200, 204)
