"""
ip_sakti.utils.session_manager — Persistent Browser Session Management.

Creates, validates, and revokes server-side session tokens that survive
Streamlit page refreshes. Tokens are stored in the SQLite ``user_sessions``
table and signed with HMAC-SHA256 to prevent forgery.

Token format (stored in browser cookie):
    <32-byte-hex-random-token>

The token is the primary key in ``user_sessions``; its HMAC signature is
computed on creation and re-verified on each validation call.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from ip_sakti.utils.db import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Session lifetime in days (default: 30)
_SESSION_LIFETIME_DAYS: int = int(os.getenv("SESSION_LIFETIME_DAYS", "30"))

# HMAC signing secret — read from environment; falls back to a stable
# machine-local secret derived from the DB path to keep things working
# out-of-the-box for development while encouraging production override.
_HMAC_SECRET: str = os.getenv("SESSION_SECRET", "ip-sakti-dev-secret-2026")

# Cookie name used by the Streamlit UI
COOKIE_NAME: str = "ipsakti_session"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sign_token(token: str) -> str:
    """Return HMAC-SHA256 hex digest for *token* using the configured secret."""
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


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------


class SessionManager:
    """
    Manages persistent browser sessions backed by SQLite.

    Each session is identified by a 64-hex-char token stored in the browser
    cookie ``ipsakti_session``.  An HMAC signature is embedded in the
    *signed_token* value (``raw_token.signature``) to prevent cookie
    tampering.
    """

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        """Initialise SessionManager with optional DatabaseManager."""
        self.db = db_manager or DatabaseManager()
        try:
            self.db.initialise()
        except Exception as exc:
            logger.warning(f"Failed to initialise database in SessionManager: {exc}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_session(self, user_id: str) -> str:
        """
        Create a new authenticated session for *user_id*.

        Returns the *signed_token* string that should be stored in the
        browser cookie.  Format: ``<token>.<hmac>``.
        """
        raw_token = _make_token()
        signature = _sign_token(raw_token)
        signed_token = f"{raw_token}.{signature}"

        now = _now_iso()
        expires = _expiry_iso()

        try:
            conn = self.db.connection
            with conn:
                conn.execute(
                    """
                    INSERT INTO user_sessions (token, user_id, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (raw_token, user_id, now, expires),
                )
            logger.info(
                "Created session",
                extra={"user_id": user_id, "expires_at": expires},
            )
        except Exception as exc:
            logger.error(f"Error creating session for user {user_id}: {exc}")

        return signed_token

    def validate_session(self, signed_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate *signed_token* and return the associated user record, or None.

        Validation steps:
        1. Parse ``raw_token.signature`` from the cookie value.
        2. Re-compute HMAC and verify it matches the embedded signature.
        3. Look up the raw_token in ``user_sessions``.
        4. Check expiry.
        5. Join with ``users`` to return the full user dict.

        Returns ``None`` if any step fails (invalid token, expired, etc.).
        """
        if not signed_token or "." not in signed_token:
            return None

        # Split at FIRST dot only; raw_token is hex (no dots), signature is hex
        parts = signed_token.split(".", 1)
        if len(parts) != 2:
            return None

        raw_token, embedded_sig = parts

        # 1. HMAC verification
        expected_sig = _sign_token(raw_token)
        if not hmac.compare_digest(expected_sig, embedded_sig):
            logger.warning("Session token HMAC verification failed — possible tampering")
            return None

        try:
            conn = self.db.connection
            now_iso = _now_iso()

            row = conn.execute(
                """
                SELECT s.token, s.user_id, s.expires_at,
                       u.name, u.email, u.created_at AS user_created_at
                FROM user_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (raw_token, now_iso),
            ).fetchone()

            if not row:
                return None

            return {
                "id": row["user_id"],
                "name": row["name"],
                "email": row["email"],
                "created_at": row["user_created_at"],
            }

        except Exception as exc:
            logger.error(f"Error validating session token: {exc}")
            return None

    def revoke_session(self, signed_token: str) -> None:
        """
        Revoke (delete) the session identified by *signed_token*.

        Called on Logout.
        """
        if not signed_token or "." not in signed_token:
            return

        parts = signed_token.split(".", 1)
        if len(parts) != 2:
            return

        raw_token = parts[0]

        try:
            conn = self.db.connection
            with conn:
                conn.execute(
                    "DELETE FROM user_sessions WHERE token = ?",
                    (raw_token,),
                )
            logger.info("Revoked session token")
        except Exception as exc:
            logger.error(f"Error revoking session: {exc}")

    def purge_expired_sessions(self) -> int:
        """
        Delete all expired sessions from the database.

        Returns number of sessions deleted.  Safe to call periodically.
        """
        try:
            conn = self.db.connection
            with conn:
                cursor = conn.execute(
                    "DELETE FROM user_sessions WHERE expires_at <= ?",
                    (_now_iso(),),
                )
            count = cursor.rowcount
            if count > 0:
                logger.info(f"Purged {count} expired sessions")
            return count
        except Exception as exc:
            logger.error(f"Error purging expired sessions: {exc}")
            return 0
