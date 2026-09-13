"""
tests/test_auth.py — Tests for User Authentication, Security & User Chat Isolation.

Validates:
1. PBKDF2-SHA256 password hashing & verification.
2. User registration, duplicate email rejection, password confirmation, validation rules.
3. User login authentication and failure messages.
4. User session isolation & chat history scoping (User A cannot access or delete User B's chats).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ip_sakti.utils.auth import AuthService, hash_password, verify_password
from ip_sakti.utils.chat_storage import ChatStorageService
from ip_sakti.utils.db import DatabaseManager


@pytest.fixture
def temp_db():
    """Fixture creating a temporary database manager."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_auth.db"
        db = DatabaseManager(db_path=str(db_path))
        db.initialise()
        try:
            yield db
        finally:
            db.close()


@pytest.fixture
def auth_service(temp_db):
    """Fixture creating AuthService bound to temp DB."""
    return AuthService(db_manager=temp_db)


@pytest.fixture
def chat_storage(temp_db):
    """Fixture creating ChatStorageService bound to temp DB."""
    return ChatStorageService(db_manager=temp_db)


# ---------------------------------------------------------------------------
# 1. Password Hashing & Verification
# ---------------------------------------------------------------------------


def test_password_hashing():
    """Test PBKDF2 hashing, unique salting, and verification."""
    password = "SecurePassword123!"
    h1 = hash_password(password)
    h2 = hash_password(password)

    # Hashes must differ because of random salt
    assert h1 != h2
    assert "$" in h1

    # Verification must succeed for correct password
    assert verify_password(password, h1) is True
    assert verify_password(password, h2) is True

    # Verification must fail for wrong password
    assert verify_password("WrongPassword123!", h1) is False
    assert verify_password("", h1) is False
    assert verify_password("SecurePassword123!", "invalid_hash_string") is False


# ---------------------------------------------------------------------------
# 2. Registration Tests
# ---------------------------------------------------------------------------


def test_registration_success(auth_service):
    """Test registering a new user with valid details."""
    user, err = auth_service.register_user(
        name="Johney Sahayak",
        email="johney@example.com",
        password="MySecretPassword123",
        confirm_password="MySecretPassword123",
        terms_accepted=True,
    )
    assert err is None
    assert user is not None
    assert user["name"] == "Johney Sahayak"
    assert user["email"] == "johney@example.com"
    assert "id" in user
    assert "password_hash" not in user  # Ensure hash is never exposed in user dict


def test_registration_duplicate_email(auth_service):
    """Test that registering with an existing email is rejected."""
    auth_service.register_user(
        name="User One",
        email="duplicate@example.com",
        password="Password123",
        confirm_password="Password123",
    )
    user2, err2 = auth_service.register_user(
        name="User Two",
        email="DUPLICATE@example.com",  # Case insensitive check
        password="Password456",
        confirm_password="Password456",
    )
    assert user2 is None
    assert err2 == "An account with this email already exists."


def test_registration_validation_errors(auth_service):
    """Test registration validation rules (name, email, password match, terms)."""
    # Missing name
    u, err = auth_service.register_user("", "test@ex.com", "pass123", "pass123")
    assert u is None and "Full Name is required" in err

    # Invalid email
    u, err = auth_service.register_user("Name", "invalid-email", "pass123", "pass123")
    assert u is None and "valid email" in err

    # Short password
    u, err = auth_service.register_user("Name", "test@ex.com", "123", "123")
    assert u is None and "6 characters" in err

    # Password mismatch
    u, err = auth_service.register_user("Name", "test@ex.com", "pass1234", "pass5678")
    assert u is None and "do not match" in err

    # Terms not accepted
    u, err = auth_service.register_user(
        "Name", "test@ex.com", "pass1234", "pass1234", terms_accepted=False
    )
    assert u is None and "Terms of Service" in err


# ---------------------------------------------------------------------------
# 3. Authentication (Login) Tests
# ---------------------------------------------------------------------------


def test_login_success(auth_service):
    """Test valid user authentication."""
    auth_service.register_user(
        name="Valid User",
        email="valid@example.com",
        password="SecretPassword123",
        confirm_password="SecretPassword123",
    )

    user, err = auth_service.authenticate_user("valid@example.com", "SecretPassword123")
    assert err is None
    assert user is not None
    assert user["name"] == "Valid User"
    assert user["email"] == "valid@example.com"


def test_login_invalid_credentials(auth_service):
    """Test login with wrong password or non-existent user."""
    auth_service.register_user(
        name="Valid User",
        email="valid@example.com",
        password="SecretPassword123",
        confirm_password="SecretPassword123",
    )

    # Wrong password
    u1, err1 = auth_service.authenticate_user("valid@example.com", "WrongPassword")
    assert u1 is None
    assert err1 == "Incorrect email or password."

    # Non-existent user
    u2, err2 = auth_service.authenticate_user("nobody@example.com", "SecretPassword123")
    assert u2 is None
    assert err2 == "Incorrect email or password."


# ---------------------------------------------------------------------------
# 4. User Session & Chat Isolation Tests
# ---------------------------------------------------------------------------


def test_user_chat_isolation(auth_service, chat_storage):
    """
    Test that User A and User B have separate, isolated chat histories.
    User A cannot retrieve or delete User B's conversations.
    """
    # 1. Create two users
    u_a, _ = auth_service.register_user("User A", "user_a@ex.com", "pass1234", "pass1234")
    u_b, _ = auth_service.register_user("User B", "user_b@ex.com", "pass1234", "pass1234")

    user_a_id = u_a["id"]
    user_b_id = u_b["id"]

    # 2. User A creates a chat
    conv_a = chat_storage.create_conversation(title="User A Ayurvedic Research", user_id=user_a_id)
    chat_storage.add_message(conv_a["id"], "user", "How to patent Ashwagandha formulation?")

    # 3. User B creates a chat
    conv_b = chat_storage.create_conversation(title="User B Form 24D Query", user_id=user_b_id)
    chat_storage.add_message(conv_b["id"], "user", "What are Form 24D requirements?")

    # 4. Verify User A lists only User A's chats
    chats_a = chat_storage.list_conversations(user_id=user_a_id)
    chat_ids_a = [c["id"] for c in chats_a]
    assert conv_a["id"] in chat_ids_a
    assert conv_b["id"] not in chat_ids_a

    # 5. Verify User B lists only User B's chats
    chats_b = chat_storage.list_conversations(user_id=user_b_id)
    chat_ids_b = [c["id"] for c in chats_b]
    assert conv_b["id"] in chat_ids_b
    assert conv_a["id"] not in chat_ids_b

    # 6. Verify User B cannot access User A's conversation by ID
    loaded_by_b = chat_storage.get_conversation(conv_a["id"], user_id=user_b_id)
    assert loaded_by_b is None

    # 7. Verify User B cannot delete User A's conversation
    del_result = chat_storage.delete_conversation(conv_a["id"], user_id=user_b_id)
    assert del_result is False

    # 8. Verify User A CAN retrieve and delete User A's conversation
    loaded_by_a = chat_storage.get_conversation(conv_a["id"], user_id=user_a_id)
    assert loaded_by_a is not None
    assert len(loaded_by_a["messages"]) == 1

    del_a_result = chat_storage.delete_conversation(conv_a["id"], user_id=user_a_id)
    assert del_a_result is True

    # 9. Ensure conv_a is deleted for User A
    assert chat_storage.get_conversation(conv_a["id"], user_id=user_a_id) is None
