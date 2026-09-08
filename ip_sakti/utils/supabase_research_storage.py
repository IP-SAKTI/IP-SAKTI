"""
ip_sakti.utils.supabase_research_storage — Research Session & Live Source Metadata Persistence.

Persists research session queries, search modes, statuses, and live retrieved source
metadata to Supabase (public.research_sessions, public.research_sources) with SQLite fallback.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ip_sakti.utils.db import DatabaseManager
from ip_sakti.utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class SupabaseResearchStorageService:
    """
    Manages persistence of live web/patent research sessions and sources.
    """

    def __init__(
        self,
        supabase_client: Optional[SupabaseClient] = None,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        self.client = supabase_client or SupabaseClient()
        self.db = db_manager or DatabaseManager()
        self._ensure_sqlite_tables()

    def _ensure_sqlite_tables(self) -> None:
        """Create fallback SQLite tables for research sessions and sources."""
        try:
            conn = self.db.connection
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS research_sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        conversation_id TEXT,
                        query TEXT NOT NULL,
                        search_mode TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        completed_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS research_sources (
                        id TEXT PRIMARY KEY,
                        research_session_id TEXT NOT NULL,
                        source_id TEXT,
                        title TEXT NOT NULL,
                        url TEXT,
                        source_type TEXT NOT NULL,
                        authority_tier INTEGER NOT NULL,
                        snippet TEXT,
                        published_at TEXT,
                        retrieved_at TEXT NOT NULL,
                        rank INTEGER DEFAULT 0
                    )
                    """
                )
        except Exception as exc:
            logger.warning(f"Failed to ensure SQLite research tables: {exc}")

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

        if self.is_supabase_enabled and user_id:
            try:
                record = {
                    "id": session_id,
                    "user_id": user_id,
                    "query": query,
                    "search_mode": search_mode,
                    "status": "in_progress",
                    "created_at": now_iso,
                }
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

        # Local SQLite fallback
        try:
            conn = self.db.connection
            with conn:
                conn.execute(
                    """
                    INSERT INTO research_sessions (id, user_id, conversation_id, query, search_mode, status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'in_progress', ?)
                    """,
                    (session_id, user_id, conversation_id, query, search_mode, now_iso),
                )
        except Exception as exc:
            logger.warning(f"Failed to create research session in SQLite: {exc}")

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

        # SQLite fallback
        try:
            conn = self.db.connection
            with conn:
                for r in records:
                    conn.execute(
                        """
                        INSERT INTO research_sources (
                            id, research_session_id, source_id, title, url,
                            source_type, authority_tier, snippet, published_at, retrieved_at, rank
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            r["id"],
                            r["research_session_id"],
                            r["source_id"],
                            r["title"],
                            r["url"],
                            r["source_type"],
                            r["authority_tier"],
                            r["snippet"],
                            r["published_at"],
                            r["retrieved_at"],
                            r["rank"],
                        ),
                    )
        except Exception as exc:
            logger.warning(f"Failed to save research sources in SQLite: {exc}")

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
                return
            except Exception as exc:
                logger.error(f"Failed to complete research session in Supabase: {exc}")

        try:
            conn = self.db.connection
            with conn:
                conn.execute(
                    "UPDATE research_sessions SET status = ?, completed_at = ? WHERE id = ?",
                    (status, now_iso, research_session_id),
                )
        except Exception as exc:
            logger.warning(f"Failed to complete research session in SQLite: {exc}")
