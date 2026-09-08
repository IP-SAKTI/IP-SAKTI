"""
tests/test_supabase_auth.py — Unit tests for Supabase Auth adapter and user isolation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from ip_sakti.utils.supabase_auth import SupabaseAuthService
from ip_sakti.utils.supabase_client import SupabaseClient


@pytest.fixture
def mock_supabase_client():
    client = MagicMock(spec=SupabaseClient)
    client.is_configured = True
    client.url = "https://test.supabase.co"
    client.anon_key = "test-anon-key"
    client.service_role_key = "test-service-role-key"
    return client


def test_supabase_auth_registration_success(mock_supabase_client):
    mock_supabase_client.sign_up.return_value = {
        "user": {"id": "user-uuid-123"},
        "access_token": "token-xyz",
        "refresh_token": "ref-xyz",
    }
    mock_supabase_client.insert.return_value = [{"id": "user-uuid-123"}]

    auth = SupabaseAuthService(supabase_client=mock_supabase_client)
    user, err = auth.register_user(
        name="Vaidya Sharma",
        email="sharma@ayush.org",
        password="ValidPassword123!",
        confirm_password="ValidPassword123!",
        terms_accepted=True,
    )

    assert err is None
    assert user is not None
    assert user["id"] == "user-uuid-123"
    assert user["email"] == "sharma@ayush.org"
    mock_supabase_client.sign_up.assert_called_once()
    mock_supabase_client.insert.assert_called_once()


def test_supabase_auth_validation_failures(mock_supabase_client):
    auth = SupabaseAuthService(supabase_client=mock_supabase_client)

    # Empty name
    user, err = auth.register_user("", "test@test.com", "pass123", "pass123")
    assert err == "Full Name is required."

    # Invalid email
    user, err = auth.register_user("Name", "invalid-email", "pass123", "pass123")
    assert "valid email" in err

    # Short password
    user, err = auth.register_user("Name", "test@test.com", "123", "123")
    assert "at least 6 characters" in err

    # Mismatched password
    user, err = auth.register_user("Name", "test@test.com", "pass123", "pass456")
    assert "do not match" in err

    # Terms not accepted
    user, err = auth.register_user("Name", "test@test.com", "pass123", "pass123", terms_accepted=False)
    assert "accept the Terms" in err


def test_supabase_auth_login_success(mock_supabase_client):
    mock_supabase_client.sign_in_with_password.return_value = {
        "user": {
            "id": "user-uuid-456",
            "user_metadata": {"name": "Dr. Arya"},
        },
        "access_token": "valid-jwt-token",
        "refresh_token": "valid-ref-token",
    }

    auth = SupabaseAuthService(supabase_client=mock_supabase_client)
    user, err = auth.authenticate_user("arya@ayush.org", "SecurePassword123!")

    assert err is None
    assert user is not None
    assert user["id"] == "user-uuid-456"
    assert user["name"] == "Dr. Arya"
    assert user["access_token"] == "valid-jwt-token"


def test_supabase_auth_verify_session(mock_supabase_client):
    mock_supabase_client.get_user.return_value = {
        "id": "user-uuid-456",
        "email": "arya@ayush.org",
        "user_metadata": {"display_name": "Dr. Arya"},
    }

    auth = SupabaseAuthService(supabase_client=mock_supabase_client)
    session_user = auth.verify_session("valid-jwt-token")

    assert session_user is not None
    assert session_user["id"] == "user-uuid-456"
    assert session_user["name"] == "Dr. Arya"


def test_supabase_auth_sign_out(mock_supabase_client):
    mock_supabase_client.sign_out.return_value = True
    auth = SupabaseAuthService(supabase_client=mock_supabase_client)
    success = auth.sign_out("token-xyz")
    assert success is True
    mock_supabase_client.sign_out.assert_called_with("token-xyz")


def test_supabase_auth_unconfigured_fallback():
    client = MagicMock(spec=SupabaseClient)
    client.is_configured = False

    auth = SupabaseAuthService(supabase_client=client)
    # When Supabase is not configured, it falls back seamlessly to SQLite
    assert auth.is_supabase_enabled is False
