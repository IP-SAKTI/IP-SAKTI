"""
ip_sakti.utils.supabase_chat_storage — Supabase-backed Chat Storage Adapter.

Persists conversations and messages to Supabase PostgreSQL (public.conversations & public.messages)
with Row Level Security.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ip_sakti.utils.supabase_client import SupabaseClient


import uuid

def sanitize_uuid(user_id: Optional[str]) -> Optional[str]:
    """Sanitize user_id string to a valid UUID format for PostgreSQL UUID columns."""
    if not user_id:
        return None
    raw = str(user_id).strip()
    try:
        return str(uuid.UUID(raw))
    except Exception:
        pass
    cleaned = raw.replace("usr-", "").strip()
    try:
        return str(uuid.UUID(cleaned))
    except Exception:
        pass
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw))

logger = logging.getLogger(__name__)


def generate_title(query: str) -> str:
    """
    Generate a concise, deterministic title from the first user query.

    Does NOT call Gemini or external APIs.
    """
    if not query or not query.strip():
        return "New Chat"

    q_clean = query.strip()
    q_lower = q_clean.lower()

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

    if len(cleaned) > 40:
        words = cleaned[:40].rsplit(" ", 1)[0]
        cleaned = words if words else cleaned[:40]

    title = cleaned.strip().title()
    return title if title else "New Conversation"



class SupabaseChatStorageService:
    """
    Manages persistence of conversations and messages in Supabase PostgreSQL.
    """

    def __init__(
        self,
        supabase_client: Optional[SupabaseClient] = None,
    ) -> None:
        self.client = supabase_client or SupabaseClient()
        self._mem_convs: Dict[str, Dict[str, Any]] = {}
        self._mem_msgs: Dict[str, List[Dict[str, Any]]] = {}

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
        cid = conversation_id or str(uuid4())
        conv_title = title or "New Chat"
        now_iso = datetime.now(timezone.utc).isoformat()

        if not self.is_supabase_enabled:
            conv = {
                "id": cid,
                "user_id": user_id,
                "title": conv_title,
                "created_at": now_iso,
                "updated_at": now_iso,
                "messages": [],
            }
            self._mem_convs[cid] = conv
            self._mem_msgs[cid] = []
            return conv

        try:
            record: Dict[str, Any] = {
                "id": cid,
                "title": conv_title,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            clean_uid = sanitize_uuid(user_id)
            if clean_uid:
                record["user_id"] = clean_uid

            try:
                self.client.insert(
                    table="conversations",
                    data=record,
                    use_service_role=True if self.client.service_role_key else False,
                )
            except Exception as insert_exc:
                if ("23503" in str(insert_exc) or "foreign key" in str(insert_exc).lower()) and "user_id" in record:
                    record.pop("user_id", None)
                    self.client.insert(
                        table="conversations",
                        data=record,
                        use_service_role=True if self.client.service_role_key else False,
                    )
                else:
                    raise insert_exc

            conv_res = {
                "id": cid,
                "user_id": user_id,
                "title": conv_title,
                "created_at": now_iso,
                "updated_at": now_iso,
                "messages": [],
            }
            self._mem_convs[cid] = conv_res
            self._mem_msgs[cid] = []
            logger.info("Created new conversation in Supabase", extra={"conversation_id": cid, "user_id": user_id})
            return conv_res
        except Exception as exc:
            logger.error(f"Error creating conversation in Supabase: {exc}")
            conv = {
                "id": cid,
                "user_id": user_id,
                "title": conv_title,
                "created_at": now_iso,
                "updated_at": now_iso,
                "messages": [],
            }
            self._mem_convs[cid] = conv
            self._mem_msgs[cid] = []
            return conv

    def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch conversation record with all associated messages.
        """
        if not self.is_supabase_enabled:
            conv = self._mem_convs.get(conversation_id)
            if not conv:
                return None
            if user_id and conv.get("user_id") and conv.get("user_id") != user_id:
                return None
            conv["messages"] = self._mem_msgs.get(conversation_id, [])
            return conv

        try:
            params: Dict[str, Any] = {"id": f"eq.{conversation_id}", "select": "*"}
            rows = self.client.select(
                table="conversations",
                params=params,
                use_service_role=True if self.client.service_role_key else False,
            )
            if not rows:
                mem_conv = self._mem_convs.get(conversation_id)
                if mem_conv:
                    if user_id and mem_conv.get("user_id") and mem_conv.get("user_id") != user_id:
                        return None
                    mem_conv["messages"] = self._mem_msgs.get(conversation_id, [])
                    return mem_conv
                return None

            conv = rows[0]
            clean_uid = sanitize_uuid(user_id)
            if user_id and conv.get("user_id"):
                row_uid = str(conv.get("user_id"))
                if row_uid != user_id and row_uid != clean_uid:
                    return None

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
            return self._mem_convs.get(conversation_id)

    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch most recently updated conversations for the active user.
        Always scoped to user_id to prevent leaking other users' conversations.
        """
        if not user_id:
            return []

        clean_uid = sanitize_uuid(user_id)

        if not self.is_supabase_enabled:
            convs = list(self._mem_convs.values())
            convs = [c for c in convs if c.get("user_id") == user_id or (clean_uid and c.get("user_id") == clean_uid)]
            convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return convs[:limit]

        try:
            params: Dict[str, Any] = {
                "order": "updated_at.desc",
                "limit": str(limit),
                "select": "id,user_id,title,created_at,updated_at",
            }
            if clean_uid:
                params["user_id"] = f"eq.{clean_uid}"
            else:
                params["user_id"] = f"eq.{user_id}"

            rows = self.client.select(
                table="conversations",
                params=params,
                use_service_role=True if self.client.service_role_key else False,
            )

            rows = [r for r in rows if r.get("user_id") == user_id or (clean_uid and r.get("user_id") == clean_uid)]

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
            convs = list(self._mem_convs.values())
            convs = [c for c in convs if c.get("user_id") == user_id or (clean_uid and c.get("user_id") == clean_uid)]
            convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return convs[:limit]

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save a message to a conversation. Inherits user_id from parent conversation if not explicitly provided.
        """
        msg_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        content_text = content if isinstance(content, str) else json.dumps(content)

        if not self.is_supabase_enabled:
            if conversation_id not in self._mem_convs:
                self.create_conversation(title="New Chat", conversation_id=conversation_id, user_id=user_id)
            msg = {
                "id": msg_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content_text,
                "timestamp": now_iso,
                "metadata": metadata or (content if isinstance(content, dict) else None),
            }
            self._mem_msgs.setdefault(conversation_id, []).append(msg)
            if conversation_id in self._mem_convs:
                self._mem_convs[conversation_id]["updated_at"] = now_iso
                if role == "user":
                    curr_title = self._mem_convs[conversation_id].get("title", "")
                    if curr_title in ("New Chat", "New Conversation") or not curr_title:
                        self._mem_convs[conversation_id]["title"] = generate_title(content_text)
            return msg

        try:
            conv_rows = self.client.select(
                table="conversations",
                params={"id": f"eq.{conversation_id}", "select": "id,title,user_id"},
                use_service_role=True if self.client.service_role_key else False,
            )

            current_title = "New Chat"
            clean_uid = sanitize_uuid(user_id)
            if not clean_uid and conv_rows and conv_rows[0].get("user_id"):
                clean_uid = sanitize_uuid(conv_rows[0].get("user_id"))

            if not conv_rows:
                conv_data = {
                    "id": conversation_id,
                    "title": "New Chat",
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }
                if clean_uid:
                    conv_data["user_id"] = clean_uid
                try:
                    self.client.insert(
                        table="conversations",
                        data=conv_data,
                        use_service_role=True if self.client.service_role_key else False,
                    )
                except Exception as insert_exc:
                    if ("23503" in str(insert_exc) or "foreign key" in str(insert_exc).lower()) and "user_id" in conv_data:
                        conv_data.pop("user_id", None)
                        self.client.insert(
                            table="conversations",
                            data=conv_data,
                            use_service_role=True if self.client.service_role_key else False,
                        )
                    else:
                        raise insert_exc
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
            if clean_uid:
                msg_payload["user_id"] = clean_uid

            try:
                self.client.insert(
                    table="messages",
                    data=msg_payload,
                    use_service_role=True if self.client.service_role_key else False,
                )
            except Exception as insert_exc:
                if ("23503" in str(insert_exc) or "foreign key" in str(insert_exc).lower()) and "user_id" in msg_payload:
                    msg_payload.pop("user_id", None)
                    self.client.insert(
                        table="messages",
                        data=msg_payload,
                        use_service_role=True if self.client.service_role_key else False,
                    )
                else:
                    raise insert_exc
            except Exception as insert_exc:
                if ("23503" in str(insert_exc) or "foreign key" in str(insert_exc).lower()) and "user_id" in msg_payload:
                    msg_payload.pop("user_id", None)
                    self.client.insert(
                        table="messages",
                        data=msg_payload,
                        use_service_role=True if self.client.service_role_key else False,
                    )
                else:
                    raise insert_exc

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

            msg_res = {
                "id": msg_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content_text,
                "timestamp": now_iso,
                "metadata": metadata or (content if isinstance(content, dict) else None),
            }
            self._mem_msgs.setdefault(conversation_id, []).append(msg_res)
            return msg_res
        except Exception as exc:
            logger.error(f"Error adding message in Supabase: {exc}")
            msg = {
                "id": msg_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content_text,
                "timestamp": now_iso,
                "metadata": metadata or (content if isinstance(content, dict) else None),
            }
            self._mem_msgs.setdefault(conversation_id, []).append(msg)
            return msg

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a conversation and its messages from storage if user owns it.
        """
        # ── Memory store: enforce ownership before deleting ───────────────────
        if not self.is_supabase_enabled:
            conv = self._mem_convs.get(conversation_id)
            if conv is None:
                return False
            # Enforce ownership: if a user_id is provided and the conversation
            # belongs to a different user, deny deletion.
            if user_id and conv.get("user_id") and conv.get("user_id") != user_id:
                return False
            self._mem_convs.pop(conversation_id, None)
            self._mem_msgs.pop(conversation_id, None)
            return True

        # ── Supabase path: attempt deletion (RLS enforces ownership) ─────────
        # Also clean memory cache
        self._mem_convs.pop(conversation_id, None)
        self._mem_msgs.pop(conversation_id, None)

        try:
            params: Dict[str, Any] = {"id": f"eq.{conversation_id}"}
            if user_id:
                params["user_id"] = f"eq.{user_id}"

            return self.client.delete(
                table="conversations",
                params=params,
                use_service_role=True if self.client.service_role_key else False,
            )
        except Exception as exc:
            logger.error(f"Error deleting conversation {conversation_id} from Supabase: {exc}")
            return False

