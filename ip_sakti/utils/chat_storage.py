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
    Manages persistence of conversations and messages in Supabase PostgreSQL or local SQLite.
    """

    def __init__(self, db_manager: Any = None) -> None:
        """Initialise ChatStorageService backed by SupabaseChatStorageService or local DB."""
        self.db = db_manager
        self.db_manager = db_manager
        self.supabase_storage = SupabaseChatStorageService()

    def create_conversation(
        self,
        title: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create and persist a new conversation associated with a specific user."""
        if self.db_manager:
            try:
                import uuid
                from datetime import datetime, timezone
                cid = conversation_id or str(uuid.uuid4())
                now_iso = datetime.now(timezone.utc).isoformat()
                c_title = title or "New Research Session"
                conn = self.db_manager.connection
                with conn:
                    conn.execute(
                        "INSERT INTO conversations (id, user_id, title, agent_mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (cid, user_id, c_title, "general", now_iso, now_iso),
                    )
                return {
                    "id": cid,
                    "user_id": user_id,
                    "title": c_title,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "messages": [],
                }
            except Exception as exc:
                logger.warning(f"Local SQLite create_conversation failed: {exc}")

        return self.supabase_storage.create_conversation(title=title, conversation_id=conversation_id, user_id=user_id)

    def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch conversation record with all associated messages."""
        if self.db_manager:
            try:
                import json
                conn = self.db_manager.connection
                cur = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
                row = cur.fetchone()
                if not row:
                    return None
                if user_id and row["user_id"] != user_id:
                    return None
                msg_cur = conn.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
                messages = []
                for m in msg_cur.fetchall():
                    raw_content = m["content"]
                    try:
                        content_obj = json.loads(raw_content)
                    except Exception:
                        content_obj = raw_content

                    msg_data = {
                        "id": m["id"],
                        "conversation_id": m["conversation_id"],
                        "role": m["role"],
                        "content": content_obj,
                        "created_at": m["created_at"],
                    }
                    if isinstance(content_obj, dict):
                        msg_data["metadata"] = content_obj
                    messages.append(msg_data)

                return {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "messages": messages,
                }
            except Exception as exc:
                logger.warning(f"Local SQLite get_conversation failed: {exc}")

        return self.supabase_storage.get_conversation(conversation_id=conversation_id, user_id=user_id)

    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch most recently updated conversations for the active user."""
        if self.db_manager:
            try:
                conn = self.db_manager.connection
                if user_id:
                    cur = conn.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?", (user_id, limit))
                else:
                    cur = conn.execute("SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,))
                results = []
                for row in cur.fetchall():
                    results.append({
                        "id": row["id"],
                        "user_id": row["user_id"],
                        "title": row["title"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    })
                return results
            except Exception as exc:
                logger.warning(f"Local SQLite list_conversations failed: {exc}")

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
        if self.db_manager:
            try:
                import uuid, json
                from datetime import datetime, timezone
                mid = str(uuid.uuid4())
                now_iso = datetime.now(timezone.utc).isoformat()
                str_content = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
                conn = self.db_manager.connection
                with conn:
                    conn.execute(
                        "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                        (mid, conversation_id, role, str_content, now_iso),
                    )
                    conn.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (now_iso, conversation_id),
                    )

                    # Auto-update title on first user turn if title is default
                    if role == "user" and isinstance(content, str) and content.strip():
                        cur = conn.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
                        c_row = cur.fetchone()
                        if c_row and c_row["title"] in ("New Research Session", "New Chat", ""):
                            new_title = generate_title(content)
                            conn.execute(
                                "UPDATE conversations SET title = ? WHERE id = ?",
                                (new_title, conversation_id),
                            )

                return {
                    "id": mid,
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata or (content if isinstance(content, dict) else None),
                    "created_at": now_iso,
                }
            except Exception as exc:
                logger.warning(f"Local SQLite add_message failed: {exc}")

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
        if self.db_manager:
            try:
                conn = self.db_manager.connection
                if user_id:
                    cur = conn.execute("SELECT user_id FROM conversations WHERE id = ?", (conversation_id,))
                    row = cur.fetchone()
                    if not row or row["user_id"] != user_id:
                        return False
                with conn:
                    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                    cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                    return cur.rowcount > 0
            except Exception as exc:
                logger.warning(f"Local SQLite delete_conversation failed: {exc}")
                return False

        return self.supabase_storage.delete_conversation(conversation_id=conversation_id, user_id=user_id)



