"""
tests/test_session_manager.py — Tests for Persistent Browser Session Manager.

Validates token creation, HMAC verification, session validation,
revocation, expiry, and DB error fallback.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from ip_sakti.utils.db import DatabaseManager
from ip_sakti.utils.auth import AuthService
from ip_sakti.utils.session_manager import SessionManager


@pytest.fixture
def session_db():
    """Temporary SQLite DB with an existing user for session testing."""
    with tempfile.TemporaryDirectory() as d:
        db = DatabaseManager(db_path=str(Path(d) / "session_test.db"))
        db.initialise()
        auth = AuthService(db_manager=db)
        user, _ = auth.register_user(
            "Session Tester", "session@test.com", "pass1234", "pass1234"
        )
        yield db, user
        db.close()


def test_create_and_validate_session(session_db):
    """Session is created and validated successfully."""
    db, user = session_db
    mgr = SessionManager(db_manager=db)

    token = mgr.create_session(user["id"])
    assert "." in token  # signed_token format: raw.sig

    validated = mgr.validate_session(token)
    assert validated is not None
    assert validated["id"] == user["id"]
    assert validated["name"] == "Session Tester"
    assert validated["email"] == "session@test.com"


def test_invalid_hmac_rejected(session_db):
    """Token with tampered HMAC is rejected."""
    db, user = session_db
    mgr = SessionManager(db_manager=db)

    token = mgr.create_session(user["id"])
    # Tamper with the HMAC portion
    raw, sig = token.split(".", 1)
    tampered = f"{raw}.{'a' * len(sig)}"

    result = mgr.validate_session(tampered)
    assert result is None


def test_tampered_token_id_rejected(session_db):
    """Token with swapped raw token (but original HMAC) is rejected."""
    db, user = session_db
    mgr = SessionManager(db_manager=db)

    token1 = mgr.create_session(user["id"])
    token2 = mgr.create_session(user["id"])

    raw1, sig1 = token1.split(".", 1)
    raw2, _ = token2.split(".", 1)
    # Swap raw token but keep original sig
    cross_token = f"{raw2}.{sig1}"

    result = mgr.validate_session(cross_token)
    assert result is None  # HMAC mismatch


def test_revoke_session(session_db):
    """Revoking a session makes it invalid."""
    db, user = session_db
    mgr = SessionManager(db_manager=db)

    token = mgr.create_session(user["id"])
    assert mgr.validate_session(token) is not None

    mgr.revoke_session(token)
    assert mgr.validate_session(token) is None


def test_missing_cookie_returns_none(session_db):
    """Empty or malformed token strings return None without error."""
    db, user = session_db
    mgr = SessionManager(db_manager=db)

    assert mgr.validate_session("") is None
    assert mgr.validate_session("notadottoken") is None
    assert mgr.validate_session(None) is None  # type: ignore[arg-type]


def test_revoke_invalid_token_is_safe(session_db):
    """Revoking a non-existent token is a no-op (no exception)."""
    db, user = session_db
    mgr = SessionManager(db_manager=db)
    # Should not raise
    mgr.revoke_session("deadbeef.fakesig")


def test_purge_expired_sessions(session_db):
    """purge_expired_sessions removes expired rows without touching valid ones."""
    db, user = session_db
    mgr = SessionManager(db_manager=db)

    # Create a valid session
    valid_token = mgr.create_session(user["id"])

    # Manually insert an already-expired session
    raw_expired = "expiredtoken1234" * 4  # 64-char hex-like string
    past_iso = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    conn = db.connection
    with conn:
        conn.execute(
            "INSERT INTO user_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (raw_expired, user["id"], past_iso, past_iso),
        )

    purged = mgr.purge_expired_sessions()
    assert purged >= 1

    # Valid session still works
    assert mgr.validate_session(valid_token) is not None
