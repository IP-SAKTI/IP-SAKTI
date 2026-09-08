"""
ip_sakti.utils.chat_storage — Persistent Chat History & Session Storage Service.

Provides SQLite persistence for chat conversations and messages, along with
deterministic title generation and non-blocking error handling.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ip_sakti.utils.db import DatabaseManager

logger = logging.getLogger(__name__)


def generate_title(query: str) -> str:
    """
    Generate a concise, deterministic title from the first user query.

    Does NOT call Gemini or external APIs.

    Examples
    --------
    "Can I patent an Ayurvedic formulation?" -> "Ayurvedic Patent Eligibility"
    "What are the requirements for Form 24D?" -> "Form 24D Requirements"
    "How does TKDL affect patentability?"    -> "TKDL & Patentability"
    """
    if not query or not query.strip():
        return "New Chat"

    q_clean = query.strip()
    q_lower = q_clean.lower()

    # Rule-based pattern matching for common domain queries
    if "patent" in q_lower and ("ayurved" in q_lower or "formulation" in q_lower or "herb" in q_lower):
        return "Ayurvedic Patent Eligibility"
    elif "24d" in q_lower or "form 24" in q_lower:
        return "Form 24D Requirements"
    elif "tkdl" in q_lower or "traditional knowledge" in q_lower:
        return "TKDL & Patentability"
    elif "abs" in q_lower or "biodiversity" in q_lower or "nba" in q_lower or "benefit sharing" in q_lower:
        return "NBA & ABS Compliance"
    elif "manufactur" in q_lower or "licens" in q_lower or "rule 158" in q_lower:
        return "Ayurvedic Manufacturing License"
    elif "trademark" in q_lower or "brand" in q_lower:
        return "Ayurvedic Trademark & Brand"
    elif "section 3" in q_lower or "3(p)" in q_lower:
        return "Section 3(p) TK Guidance"

    # Generic deterministic cleaning
    # Remove standard question prefixes
    prefixes = [
        r"^can i patent\s+",
        r"^is it possible to patent\s+",
        r"^what are the requirements for\s+",
        r"^how does\s+",
        r"^what is\s+",
        r"^how to\s+",
        r"^can i\s+",
        r"^tell me about\s+",
        r"^explain\s+",
    ]
    cleaned = q_clean
    for pat in prefixes:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.rstrip("?.! ")
    if not cleaned:
        cleaned = q_clean.rstrip("?.! ")

    # Truncate to ~40 characters safely at word boundary
    if len(cleaned) > 40:
        words = cleaned[:40].rsplit(" ", 1)[0]
        cleaned = words if words else cleaned[:40]

    # Title-case first letter of each word
    title = cleaned.strip().title()
    return title if title else "New Conversation"


class ChatStorageService:
    """
    Manages persistence of conversations and messages in SQLite database.
    """

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        """Initialise ChatStorageService with optional DatabaseManager."""
        self.db = db_manager or DatabaseManager()
        try:
            self.db.initialise()
        except Exception as exc:
            logger.warning(f"Failed to initialise database in ChatStorageService: {exc}")

    def create_conversation(
        self,
        title: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create and persist a new conversation associated with a specific user.

        Returns conversation record dict.
        """
        cid = conversation_id or str(uuid4())
        conv_title = title or "New Chat"
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            conn = self.db.connection
            with conn:
                conn.execute(
                    """
                    INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (cid, user_id, conv_title, now_iso, now_iso),
                )
            logger.info("Created new conversation", extra={"conversation_id": cid, "user_id": user_id, "title": conv_title})
        except Exception as exc:
            logger.error(f"Error creating conversation in DB: {exc}")

        return {
            "id": cid,
            "user_id": user_id,
            "title": conv_title,
            "created_at": now_iso,
            "updated_at": now_iso,
            "messages": [],
        }

    def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch conversation record with all associated messages.

        Validates user ownership if user_id is provided.
        """
        try:
            conn = self.db.connection
            if user_id:
                row = conn.execute(
                    "SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE id = ? AND user_id = ?",
                    (conversation_id, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE id = ?",
                    (conversation_id,),
                ).fetchone()

            if not row:
                return None

            msg_rows = conn.execute(
                """
                SELECT id, conversation_id, role, content, timestamp, metadata_json
                FROM messages
                WHERE conversation_id = ?
                ORDER BY rowid ASC
                """,
                (conversation_id,),
            ).fetchall()

            messages = []
            for r in msg_rows:
                meta = None
                if r["metadata_json"]:
                    try:
                        meta = json.loads(r["metadata_json"])
                    except Exception:
                        meta = None
                messages.append({
                    "id": r["id"],
                    "conversation_id": r["conversation_id"],
                    "role": r["role"],
                    "content": r["content"],
                    "timestamp": r["timestamp"],
                    "metadata": meta,
                })

            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "messages": messages,
            }
        except Exception as exc:
            logger.error(f"Error reading conversation {conversation_id} from DB: {exc}")
            return None

    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch most recently updated conversations for the active user.
        """
        try:
            conn = self.db.connection
            if user_id:
                rows = conn.execute(
                    """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM conversations
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM conversations
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                })
            return results
        except Exception as exc:
            logger.error(f"Error listing conversations from DB: {exc}")
            return []

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

        If role is 'user' and the conversation has default title 'New Chat',
        automatically generates title from the user query.
        """
        msg_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        content_text = content if isinstance(content, str) else json.dumps(content)
        meta_json = json.dumps(metadata) if metadata else None

        if isinstance(content, dict) and metadata is None:
            meta_json = json.dumps(content)

        try:
            conn = self.db.connection
            with conn:
                conv = conn.execute(
                    "SELECT id, title FROM conversations WHERE id = ?",
                    (conversation_id,),
                ).fetchone()

                if not conv:
                    conn.execute(
                        """
                        INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (conversation_id, user_id, "New Chat", now_iso, now_iso),
                    )
                    current_title = "New Chat"
                else:
                    current_title = conv["title"]

                conn.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (msg_id, conversation_id, role, content_text, now_iso, meta_json),
                )

                new_title = current_title
                if role == "user" and (current_title in ("New Chat", "New Conversation") or not current_title):
                    new_title = generate_title(content_text if isinstance(content_text, str) else "")
                    conn.execute(
                        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                        (new_title, now_iso, conversation_id),
                    )
                else:
                    conn.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (now_iso, conversation_id),
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
            logger.error(f"Error adding message to conversation {conversation_id}: {exc}")
            return {
                "id": msg_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content_text,
                "timestamp": now_iso,
                "metadata": None,
            }

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a conversation and its messages from storage if user owns it.
        """
        try:
            conn = self.db.connection
            with conn:
                if user_id:
                    conn.execute(
                        "DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE id = ? AND user_id = ?)",
                        (conversation_id, user_id),
                    )
                    cursor = conn.execute(
                        "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                        (conversation_id, user_id),
                    )
                else:
                    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                    cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Deleted conversation", extra={"conversation_id": conversation_id, "user_id": user_id})
            return deleted
        except Exception as exc:
            logger.error(f"Error deleting conversation {conversation_id}: {exc}")
            return False


