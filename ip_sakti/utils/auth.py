"""
ip_sakti.utils.auth — Authentication & User Security Service.

Implements user registration, credential verification, and session management
backed by Supabase Auth (auth.users & public.profiles).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from ip_sakti.utils.supabase_auth import SupabaseAuthService

logger = logging.getLogger(__name__)


class AuthService:
    """
    Manages user authentication and profile persistence in Supabase Auth & PostgreSQL.
    """

    def __init__(self, db_manager: Any = None) -> None:
        """Initialise AuthService backed by SupabaseAuthService."""
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
        Register a new user via Supabase Auth.
        """
        return self.supabase_auth.register_user(
            name=name,
            email=email,
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
        Authenticate a user by email and password.
        """
        return self.supabase_auth.authenticate_user(email=email, password=password)

    def verify_session(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify an authenticated session token via Supabase Auth.
        """
        return self.supabase_auth.verify_session(access_token)

    def sign_out(self, access_token: Optional[str] = None) -> bool:
        """
        Sign out session from Supabase Auth.
        """
        return self.supabase_auth.sign_out(access_token)

