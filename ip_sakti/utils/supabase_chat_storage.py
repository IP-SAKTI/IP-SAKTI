"""
ip_sakti.utils.supabase_chat_storage — Supabase-backed Chat Storage Adapter.

Preserves the EXACT public interface of ChatStorageService while persisting
conversations and messages to Supabase with Row Level Security and SQLite fallback.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ip_sakti.utils.chat_storage import ChatStorageService as SQLiteChatStorageService, generate_title
from ip_sakti.utils.db import DatabaseManager
from ip_sakti.utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class SupabaseChatStorageService:
    """
    Manages persistence of conversations and messages in Supabase with SQLite fallback.
    """

    def __init__(
        self,
        supabase_client: Optional[SupabaseClient] = None,
        fallback_service: Optional[SQLiteChatStorageService] = None,
    ) -> None:
        self.client = supabase_client or SupabaseClient()
        self.fallback = fallback_service or SQLiteChatStorageService(db_manager=DatabaseManager())

    @property
    def is_supabase_enabled(self) -> bool:
        """Check if Supabase storage is enabled and configured."""
        return self.client.is_configured

    def create_conversation(
        self,
        title: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create and persist a new conversation associated with a specific user.
        """
        if not self.is_supabase_enabled:
            return self.fallback.create_conversation(title=title, conversation_id=conversation_id, user_id=user_id)

        cid = conversation_id or str(uuid4())
        conv_title = title or "New Chat"
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            record: Dict[str, Any] = {
                "id": cid,
                "title": conv_title,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            if user_id:
                record["user_id"] = user_id

            self.client.insert(
                table="conversations",
                data=record,
                use_service_role=True if self.client.service_role_key else False,
            )
            logger.info("Created new conversation in Supabase", extra={"conversation_id": cid, "user_id": user_id})
            return {
                "id": cid,
                "user_id": user_id,
                "title": conv_title,
                "created_at": now_iso,
                "updated_at": now_iso,
                "messages": [],
            }
        except Exception as exc:
            logger.error(f"Error creating conversation in Supabase: {exc}. Falling back to SQLite.")
            return self.fallback.create_conversation(title=title, conversation_id=conversation_id, user_id=user_id)

    def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch conversation record with all associated messages.
        """
        if not self.is_supabase_enabled:
            return self.fallback.get_conversation(conversation_id=conversation_id, user_id=user_id)

        try:
            params: Dict[str, Any] = {"id": f"eq.{conversation_id}", "select": "*"}
            if user_id:
                params["user_id"] = f"eq.{user_id}"

            rows = self.client.select(
                table="conversations",
                params=params,
                use_service_role=True if self.client.service_role_key else False,
            )
            if not rows:
                # If not found in Supabase, also check fallback
                return self.fallback.get_conversation(conversation_id=conversation_id, user_id=user_id)

            conv = rows[0]

            # Fetch messages
            msg_params: Dict[str, Any] = {
                "conversation_id": f"eq.{conversation_id}",
                "order": "created_at.asc",
                "select": "*",
            }
            msg_rows = self.client.select(
                table="messages",
                params=msg_params,
                use_service_role=True if self.client.service_role_key else False,
            )

            messages = []
            for r in msg_rows:
                messages.append({
                    "id": r.get("id"),
                    "conversation_id": r.get("conversation_id"),
                    "role": r.get("role"),
                    "content": r.get("content"),
                    "timestamp": r.get("created_at"),
                    "metadata": r.get("metadata"),
                })

            return {
                "id": conv.get("id"),
                "user_id": conv.get("user_id"),
                "title": conv.get("title"),
                "created_at": conv.get("created_at"),
                "updated_at": conv.get("updated_at"),
                "messages": messages,
            }
        except Exception as exc:
            logger.error(f"Error fetching conversation {conversation_id} from Supabase: {exc}")
            return self.fallback.get_conversation(conversation_id=conversation_id, user_id=user_id)

    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch most recently updated conversations for the active user.
        """
        if not self.is_supabase_enabled:
            return self.fallback.list_conversations(user_id=user_id, limit=limit)

        try:
            params: Dict[str, Any] = {
                "order": "updated_at.desc",
                "limit": str(limit),
                "select": "id,user_id,title,created_at,updated_at",
            }
            if user_id:
                params["user_id"] = f"eq.{user_id}"

            rows = self.client.select(
                table="conversations",
                params=params,
                use_service_role=True if self.client.service_role_key else False,
            )
            if not rows and user_id is None:
                return self.fallback.list_conversations(user_id=user_id, limit=limit)

            return [
                {
                    "id": r.get("id"),
                    "user_id": r.get("user_id"),
                    "title": r.get("title"),
                    "created_at": r.get("created_at"),
                    "updated_at": r.get("updated_at"),
                }
                for r in rows
            ]
        except Exception as exc:
            logger.error(f"Error listing conversations from Supabase: {exc}")
            return self.fallback.list_conversations(user_id=user_id, limit=limit)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save a message to a conversation.
        """
        if not self.is_supabase_enabled:
            return self.fallback.add_message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=metadata,
                user_id=user_id,
            )

        msg_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        content_text = content if isinstance(content, str) else json.dumps(content)

        try:
            # Ensure conversation exists
            conv_rows = self.client.select(
                table="conversations",
                params={"id": f"eq.{conversation_id}", "select": "id,title"},
                use_service_role=True if self.client.service_role_key else False,
            )

            current_title = "New Chat"
            if not conv_rows:
                conv_data = {
                    "id": conversation_id,
                    "title": "New Chat",
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }
                if user_id:
                    conv_data["user_id"] = user_id
                self.client.insert(
                    table="conversations",
                    data=conv_data,
                    use_service_role=True if self.client.service_role_key else False,
                )
            else:
                current_title = conv_rows[0].get("title", "New Chat")

            msg_payload: Dict[str, Any] = {
                "id": msg_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content_text,
                "created_at": now_iso,
                "metadata": metadata or (content if isinstance(content, dict) else None),
            }
            if user_id:
                msg_payload["user_id"] = user_id

            self.client.insert(
                table="messages",
                data=msg_payload,
                use_service_role=True if self.client.service_role_key else False,
            )

            # Update conversation updated_at and deterministic title
            if role == "user" and (current_title in ("New Chat", "New Conversation") or not current_title):
                new_title = generate_title(content_text if isinstance(content_text, str) else "")
                self.client.update(
                    table="conversations",
                    data={"title": new_title, "updated_at": now_iso},
                    params={"id": f"eq.{conversation_id}"},
                    use_service_role=True if self.client.service_role_key else False,
                )
            else:
                self.client.update(
                    table="conversations",
                    data={"updated_at": now_iso},
                    params={"id": f"eq.{conversation_id}"},
                    use_service_role=True if self.client.service_role_key else False,
                )

            return {
                "id": msg_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content_text,
                "timestamp": now_iso,
                "metadata": metadata or (content if isinstance(content, dict) else None),
            }
        except Exception as exc:
            logger.error(f"Error adding message in Supabase: {exc}. Falling back to SQLite.")
            return self.fallback.add_message(
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
        """
        Delete a conversation and its messages from storage if user owns it.
        """
        if not self.is_supabase_enabled:
            return self.fallback.delete_conversation(conversation_id=conversation_id, user_id=user_id)

        try:
            params: Dict[str, Any] = {"id": f"eq.{conversation_id}"}
            if user_id:
                params["user_id"] = f"eq.{user_id}"

            deleted = self.client.delete(
                table="conversations",
                params=params,
                use_service_role=True if self.client.service_role_key else False,
            )
            # Also clean up local SQLite if present
            self.fallback.delete_conversation(conversation_id=conversation_id, user_id=user_id)
            return deleted
        except Exception as exc:
            logger.error(f"Error deleting conversation {conversation_id} from Supabase: {exc}")
            return self.fallback.delete_conversation(conversation_id=conversation_id, user_id=user_id)
