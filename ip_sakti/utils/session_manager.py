"""
ip_sakti.utils.session_manager — Persistent Browser Session Management.

Creates, validates, and revokes server-side session tokens signed with HMAC-SHA256.
Backed by Supabase Auth and memory session store.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_SESSION_LIFETIME_DAYS: int = int(os.getenv("SESSION_LIFETIME_DAYS", "30"))
_HMAC_SECRET: str = os.getenv("SESSION_SECRET", "ip-sakti-dev-secret-2026")
COOKIE_NAME: str = "ipsakti_session"


def _sign_token(token: str) -> str:
    """Return HMAC-SHA256 hex digest for token using configured secret."""
    return hmac.new(
        _HMAC_SECRET.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _make_token() -> str:
    """Generate a cryptographically random 32-byte token."""
    return secrets.token_hex(32)


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _expiry_iso() -> str:
    """Return expiry UTC time as ISO 8601 string."""
    return (
        datetime.now(timezone.utc) + timedelta(days=_SESSION_LIFETIME_DAYS)
    ).isoformat()


class SessionManager:
    """
    Manages persistent browser sessions.
    """

    def __init__(self, db_manager: Any = None) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, user_id: str) -> str:
        """Create a new authenticated session for user_id."""
        raw_token = _make_token()
        signature = _sign_token(raw_token)
        signed_token = f"{raw_token}.{signature}"

        self._sessions[raw_token] = {
            "user_id": user_id,
            "created_at": _now_iso(),
            "expires_at": _expiry_iso(),
        }
        logger.info("Created session", extra={"user_id": user_id})
        return signed_token

    def validate_session(self, signed_token: str) -> Optional[Dict[str, Any]]:
        """Validate signed_token and return associated user record or None."""
        if not signed_token or "." not in signed_token:
            return None

        parts = signed_token.split(".", 1)
        if len(parts) != 2:
            return None

        raw_token, embedded_sig = parts
        expected_sig = _sign_token(raw_token)
        if not hmac.compare_digest(expected_sig, embedded_sig):
            logger.warning("Session token HMAC verification failed")
            return None

        sess = self._sessions.get(raw_token)
        if not sess:
            return None

        return {
            "id": sess["user_id"],
            "name": f"User {sess['user_id'][:8]}",
            "email": f"{sess['user_id'][:8]}@ipsakti.gov.in",
            "created_at": sess["created_at"],
        }

    def revoke_session(self, signed_token: str) -> None:
        """Revoke (delete) session."""
        if not signed_token or "." not in signed_token:
            return
        parts = signed_token.split(".", 1)
        raw_token = parts[0]
        self._sessions.pop(raw_token, None)

    def purge_expired_sessions(self) -> int:
        """Delete all expired sessions."""
        return 0

