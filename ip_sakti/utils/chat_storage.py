"""
ip_sakti.utils.chat_storage — Persistent Chat History & Session Storage Service.

Provides persistence for chat conversations and messages backed by Supabase PostgreSQL,
along with deterministic title generation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ip_sakti.utils.supabase_chat_storage import SupabaseChatStorageService, generate_title

logger = logging.getLogger(__name__)






class ChatStorageService:
    """
    Manages persistence of conversations and messages in Supabase PostgreSQL.
    """

    def __init__(self, db_manager: Any = None) -> None:
        """Initialise ChatStorageService backed by SupabaseChatStorageService."""
        self.supabase_storage = SupabaseChatStorageService()

    def create_conversation(
        self,
        title: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create and persist a new conversation associated with a specific user."""
        return self.supabase_storage.create_conversation(title=title, conversation_id=conversation_id, user_id=user_id)

    def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch conversation record with all associated messages."""
        return self.supabase_storage.get_conversation(conversation_id=conversation_id, user_id=user_id)

    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch most recently updated conversations for the active user."""
        return self.supabase_storage.list_conversations(user_id=user_id, limit=limit)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a message to a conversation."""
        return self.supabase_storage.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
            user_id=user_id,
        )

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Delete a conversation and its messages from storage if user owns it."""
        return self.supabase_storage.delete_conversation(conversation_id=conversation_id, user_id=user_id)



