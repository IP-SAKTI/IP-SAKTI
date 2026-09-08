"""
tests/test_supabase_chat_storage.py — Unit tests for Supabase Chat Storage adapter and user isolation.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from ip_sakti.utils.supabase_chat_storage import SupabaseChatStorageService
from ip_sakti.utils.supabase_client import SupabaseClient


@pytest.fixture
def mock_supabase_client():
    client = MagicMock(spec=SupabaseClient)
    client.is_configured = True
    client.url = "https://test.supabase.co"
    client.anon_key = "test-anon-key"
    client.service_role_key = "test-service-role-key"
    return client


def test_supabase_create_conversation(mock_supabase_client):
    mock_supabase_client.insert.return_value = [{"id": "conv-123"}]
    storage = SupabaseChatStorageService(supabase_client=mock_supabase_client)

    conv = storage.create_conversation(title="Ayurvedic Patent Eligibility", user_id="user-1")

    assert conv["title"] == "Ayurvedic Patent Eligibility"
    assert conv["user_id"] == "user-1"
    mock_supabase_client.insert.assert_called_once()


def test_supabase_get_conversation_with_user_isolation(mock_supabase_client):
    # Mock return for user-1
    mock_supabase_client.select.side_effect = [
        [{"id": "conv-123", "user_id": "user-1", "title": "Section 3(p) Guidance", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}],
        [{"id": "msg-1", "conversation_id": "conv-123", "role": "user", "content": "Can I patent this?", "created_at": "2026-01-01T00:00:00Z", "metadata": None}],
    ]

    storage = SupabaseChatStorageService(supabase_client=mock_supabase_client)
    conv = storage.get_conversation("conv-123", user_id="user-1")

    assert conv is not None
    assert conv["id"] == "conv-123"
    assert len(conv["messages"]) == 1
    assert conv["messages"][0]["content"] == "Can I patent this?"


def test_supabase_list_conversations_user_scoped(mock_supabase_client):
    mock_supabase_client.select.return_value = [
        {"id": "conv-1", "user_id": "user-1", "title": "Chat 1", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-02T00:00:00Z"},
        {"id": "conv-2", "user_id": "user-1", "title": "Chat 2", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
    ]

    storage = SupabaseChatStorageService(supabase_client=mock_supabase_client)
    chats = storage.list_conversations(user_id="user-1", limit=10)

    assert len(chats) == 2
    assert chats[0]["title"] == "Chat 1"
    mock_supabase_client.select.assert_called_once()
    # Confirm user_id is in params
    call_kwargs = mock_supabase_client.select.call_args[1]
    assert "user_id" in call_kwargs["params"]


def test_supabase_add_message_and_title_update(mock_supabase_client):
    # Mock conversation check: exists with title "New Chat"
    mock_supabase_client.select.return_value = [{"id": "conv-999", "title": "New Chat"}]
    mock_supabase_client.insert.return_value = [{"id": "msg-999"}]
    mock_supabase_client.update.return_value = [{"id": "conv-999"}]

    storage = SupabaseChatStorageService(supabase_client=mock_supabase_client)
    msg = storage.add_message(
        conversation_id="conv-999",
        role="user",
        content="What are the requirements for Form 24D in Ayurvedic licensing?",
        user_id="user-1",
    )

    assert msg["role"] == "user"
    assert "Form 24D" in msg["content"]
    # Check title update was called with deterministic title "Form 24D Requirements"
    update_calls = mock_supabase_client.update.call_args_list
    assert len(update_calls) == 1
    updated_data = update_calls[0][1]["data"]
    assert updated_data["title"] == "Form 24D Requirements"


def test_supabase_delete_conversation(mock_supabase_client):
    mock_supabase_client.delete.return_value = True

    storage = SupabaseChatStorageService(supabase_client=mock_supabase_client)
    success = storage.delete_conversation("conv-123", user_id="user-1")

    assert success is True
    mock_supabase_client.delete.assert_called_once()
