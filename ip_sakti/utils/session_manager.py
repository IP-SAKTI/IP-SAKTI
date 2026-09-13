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
        self.db_manager = db_manager
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, user_id: str) -> str:
        """Create a new authenticated session for user_id."""
        raw_token = _make_token()
        signature = _sign_token(raw_token)
        signed_token = f"{raw_token}.{signature}"
        created_at = _now_iso()
        expires_at = _expiry_iso()

        self._sessions[raw_token] = {
            "user_id": user_id,
            "created_at": created_at,
            "expires_at": expires_at,
        }

        if self.db_manager:
            try:
                conn = self.db_manager.connection
                with conn:
                    conn.execute(
                        "INSERT INTO user_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                        (raw_token, user_id, created_at, expires_at),
                    )
            except Exception as exc:
                logger.warning(f"Failed to persist session to DB: {exc}")

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

        user_id = None
        created_at = None

        if self.db_manager:
            try:
                conn = self.db_manager.connection
                cur = conn.execute(
                    "SELECT user_id, created_at, expires_at FROM user_sessions WHERE token = ?",
                    (raw_token,),
                )
                row = cur.fetchone()
                if row:
                    expires_at_str = row["expires_at"]
                    if expires_at_str:
                        exp_dt = datetime.fromisoformat(expires_at_str)
                        if exp_dt.tzinfo is None:
                            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                        if exp_dt < datetime.now(timezone.utc):
                            return None
                    user_id = row["user_id"]
                    created_at = row["created_at"]
            except Exception as exc:
                logger.warning(f"Failed to query session from DB: {exc}")

        if not user_id:
            sess = self._sessions.get(raw_token)
            if not sess:
                return None
            user_id = sess["user_id"]
            created_at = sess["created_at"]

        name = f"User {user_id[:8]}"
        email = f"{user_id[:8]}@ipsakti.gov.in"

        if self.db_manager and user_id:
            try:
                conn = self.db_manager.connection
                cur = conn.execute(
                    "SELECT id, email, full_name FROM users WHERE id = ?",
                    (user_id,),
                )
                urow = cur.fetchone()
                if urow:
                    if urow["full_name"]:
                        name = urow["full_name"]
                    if urow["email"]:
                        email = urow["email"]
            except Exception as exc:
                logger.warning(f"Failed to query user details for session: {exc}")

        return {
            "id": user_id,
            "name": name,
            "email": email,
            "created_at": created_at,
        }

    def revoke_session(self, signed_token: str) -> None:
        """Revoke (delete) session."""
        if not signed_token or "." not in signed_token:
            return
        parts = signed_token.split(".", 1)
        raw_token = parts[0]
        self._sessions.pop(raw_token, None)

        if self.db_manager:
            try:
                conn = self.db_manager.connection
                with conn:
                    conn.execute("DELETE FROM user_sessions WHERE token = ?", (raw_token,))
            except Exception as exc:
                logger.warning(f"Failed to revoke session in DB: {exc}")

    def purge_expired_sessions(self) -> int:
        """Delete all expired sessions."""
        purged_count = 0
        now_str = _now_iso()

        expired_memory = [
            t for t, s in self._sessions.items() if s.get("expires_at", "") < now_str
        ]
        for t in expired_memory:
            self._sessions.pop(t, None)

        if self.db_manager:
            try:
                conn = self.db_manager.connection
                with conn:
                    cur = conn.execute(
                        "DELETE FROM user_sessions WHERE expires_at < ?",
                        (now_str,),
                    )
                    purged_count = cur.rowcount
            except Exception as exc:
                logger.warning(f"Failed to purge expired sessions in DB: {exc}")

        return purged_count


