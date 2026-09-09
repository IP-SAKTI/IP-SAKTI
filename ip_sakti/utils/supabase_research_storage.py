"""
ip_sakti.utils.supabase_research_storage — Research Session & Live Source Metadata Persistence.

Persists research session queries, search modes, statuses, and live retrieved source
metadata to Supabase PostgreSQL (public.research_sessions, public.research_sources).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ip_sakti.utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class SupabaseResearchStorageService:
    """
    Manages persistence of live web/patent research sessions and sources in Supabase PostgreSQL.
    """

    def __init__(
        self,
        supabase_client: Optional[SupabaseClient] = None,
        db_manager: Any = None,
    ) -> None:
        self.client = supabase_client or SupabaseClient()

    @property
    def is_supabase_enabled(self) -> bool:
        """Check if Supabase storage is available."""
        return self.client.is_configured

    def create_session(
        self,
        query: str,
        search_mode: str = "hybrid",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        """
        Create and record a new research session.
        """
        session_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.is_supabase_enabled:
            try:
                record = {
                    "id": session_id,
                    "query": query,
                    "search_mode": search_mode,
                    "status": "in_progress",
                    "created_at": now_iso,
                }
                if user_id:
                    record["user_id"] = user_id
                if conversation_id:
                    record["conversation_id"] = conversation_id
                self.client.insert(
                    table="research_sessions",
                    data=record,
                    use_service_role=True if self.client.service_role_key else False,
                )
                return session_id
            except Exception as exc:
                logger.error(f"Failed to create research session in Supabase: {exc}")

        return session_id

    def save_sources(
        self,
        research_session_id: str,
        sources: List[Dict[str, Any]],
    ) -> None:
        """
        Save retrieved live research sources for a session.
        """
        if not sources:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        records = []
        for idx, src in enumerate(sources):
            records.append({
                "id": str(uuid4()),
                "research_session_id": research_session_id,
                "source_id": src.get("source_id"),
                "title": src.get("title") or "Untitled Source",
                "url": src.get("url"),
                "source_type": src.get("source_type") or "web",
                "authority_tier": src.get("authority_tier", 3),
                "snippet": src.get("snippet") or src.get("text") or "",
                "published_at": src.get("published_at"),
                "retrieved_at": src.get("retrieved_at") or now_iso,
                "rank": src.get("rank", idx),
            })

        if self.is_supabase_enabled:
            try:
                self.client.insert(
                    table="research_sources",
                    data=records,
                    use_service_role=True if self.client.service_role_key else False,
                )
                return
            except Exception as exc:
                logger.error(f"Failed to save research sources in Supabase: {exc}")

    def complete_session(
        self,
        research_session_id: str,
        status: str = "completed",
    ) -> None:
        """
        Mark research session as completed.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.is_supabase_enabled:
            try:
                self.client.update(
                    table="research_sessions",
                    data={"status": status, "completed_at": now_iso},
                    params={"id": f"eq.{research_session_id}"},
                    use_service_role=True if self.client.service_role_key else False,
                )
            except Exception as exc:
                logger.error(f"Failed to complete research session in Supabase: {exc}")

