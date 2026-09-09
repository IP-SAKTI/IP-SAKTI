"""
ip_sakti.retrieval.live_research_manager — Orchestrates Live Research, Caching & Evidence Fusion.

Coordinates WebSearchProvider and PatentSearchProvider, determines whether queries
require live investigation under SearchMode (internal, live, hybrid), applies
time-to-live query caching, and fuses live evidence with internal Hybrid RAG results.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from ip_sakti.models.query import EvidenceChunk, SearchMode
from ip_sakti.retrieval.patent_search import PatentSearchProvider, RealPatentSearchProvider
from ip_sakti.retrieval.web_search import WebSearchProvider, RealWebSearchProvider
from ip_sakti.utils.supabase_research_storage import SupabaseResearchStorageService

logger = logging.getLogger(__name__)

# Heuristic temporal / update keywords
_LIVE_RESEARCH_TRIGGERS = [
    "latest",
    "recent",
    "current",
    "updated",
    "2024",
    "2025",
    "2026",
    "new",
    "recently",
    "amendment",
    "notification",
    "gazette",
    "guidelines",
    "fresh",
    "change",
    "modification",
]


class LiveResearchManager:
    """
    Manages live web research sessions, caching, and evidence fusion.
    """

    def __init__(
        self,
        web_provider: Optional[WebSearchProvider] = None,
        patent_provider: Optional[PatentSearchProvider] = None,
        research_storage: Optional[SupabaseResearchStorageService] = None,
        cache_ttl_seconds: int = 600,
    ) -> None:
        self.web_provider = web_provider or RealWebSearchProvider()
        self.patent_provider = patent_provider or RealPatentSearchProvider()
        self.storage = research_storage or SupabaseResearchStorageService()
        self.cache_ttl = cache_ttl_seconds
        # In-memory TTL cache: key -> (timestamp, List[EvidenceChunk])
        self._cache: Dict[str, Tuple[float, List[EvidenceChunk]]] = {}

    def should_trigger_live_research(self, query: str, search_mode: SearchMode) -> bool:
        """
        Determine whether external live research should be executed.
        """
        if search_mode == SearchMode.INTERNAL:
            return False

        if search_mode == SearchMode.LIVE:
            return True

        # For SearchMode.HYBRID:
        q_lower = query.lower()
        if any(trigger in q_lower for trigger in _LIVE_RESEARCH_TRIGGERS):
            return True

        # Also trigger if asking about patent status, specific formulations, or recent rules
        if "patent" in q_lower and ("status" in q_lower or "grant" in q_lower or "application" in q_lower):
            return True

        return False

    def conduct_live_research(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        search_mode: SearchMode = SearchMode.HYBRID,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Tuple[List[EvidenceChunk], Optional[str]]:
        """
        Execute live research across web and patent providers.

        Returns (retrieved_chunks, research_session_id).
        """
        if not self.should_trigger_live_research(query, search_mode):
            return [], None

        cache_key = f"{query.strip().lower()}:{jurisdiction or 'any'}:{search_mode.value}"
        now = time.time()

        # Check in-memory cache
        if cache_key in self._cache:
            ts, cached_chunks = self._cache[cache_key]
            if now - ts < self.cache_ttl:
                logger.info(f"Returning {len(cached_chunks)} cached live research chunks for query: {query[:30]}")
                return cached_chunks, None

        # Create research session record in persistent storage
        session_id = self.storage.create_session(
            query=query,
            search_mode=search_mode.value,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        all_live_chunks: List[EvidenceChunk] = []

        # 1. Patent search if relevant
        if "patent" in query.lower():
            try:
                patent_chunks = self.patent_provider.search(query, jurisdiction=jurisdiction, max_results=4)
                all_live_chunks.extend(patent_chunks)
            except Exception as exc:
                logger.warning(f"Patent search failed: {exc}")

        # 2. Generic Web search
        try:
            web_chunks = self.web_provider.search(query, jurisdiction=jurisdiction, max_results=6)
            all_live_chunks.extend(web_chunks)
        except Exception as exc:
            logger.warning(f"Web search failed: {exc}")

        # Record sources in storage
        if all_live_chunks:
            source_records = [
                {
                    "source_id": c.source_id,
                    "title": c.title or c.source_name,
                    "url": c.source_url,
                    "source_type": c.document_type or "web",
                    "authority_tier": 1 if c.rerank_score and c.rerank_score > 0.85 else 3,
                    "snippet": c.content,
                    "rank": idx,
                }
                for idx, c in enumerate(all_live_chunks)
            ]
            self.storage.save_sources(session_id, source_records)
            self.storage.complete_session(session_id, status="completed")
        else:
            self.storage.complete_session(session_id, status="no_results")

        # Cache live research results
        self._cache[cache_key] = (now, all_live_chunks)

        return all_live_chunks, session_id

    def fuse_evidence(
        self,
        internal_evidence: List[EvidenceChunk],
        live_evidence: List[EvidenceChunk],
        search_mode: SearchMode = SearchMode.HYBRID,
        max_total_chunks: int = 10,
    ) -> List[EvidenceChunk]:
        """
        Fuse internal Hybrid RAG evidence with live research evidence.

        Ensures unified, sequential [SOURCE_1], [SOURCE_2] labeling for citation validation.
        """
        if search_mode == SearchMode.INTERNAL or not live_evidence:
            return self._relabel_evidence(internal_evidence[:max_total_chunks])

        if search_mode == SearchMode.LIVE and live_evidence:
            # If live search returned results, prioritize them, but keep top internal as supporting grounding
            combined = live_evidence + internal_evidence
            return self._relabel_evidence(combined[:max_total_chunks])

        # For SearchMode.HYBRID:
        # Interleave or sort by rerank_score
        combined = []
        seen_keys: set[str] = set()

        # Filter duplicates across doc_id, source_url, and content prefix
        for chunk in live_evidence + internal_evidence:
            url_key = (chunk.source_url or '').strip().lower().rstrip('/')
            doc_key = (chunk.doc_id or '').strip().lower()
            text_key = chunk.content[:60].strip().lower()

            dedup_signature_1 = f"{doc_key}:{text_key}"
            dedup_signature_2 = f"{url_key}:{text_key}"

            if dedup_signature_1 in seen_keys or dedup_signature_2 in seen_keys:
                continue

            seen_keys.add(dedup_signature_1)
            if url_key:
                seen_keys.add(dedup_signature_2)
            combined.append(chunk)

        # Sort by rerank_score / authority
        combined.sort(key=lambda c: (c.rerank_score or 0.5), reverse=True)
        return self._relabel_evidence(combined[:max_total_chunks])

    def _relabel_evidence(self, chunks: List[EvidenceChunk]) -> List[EvidenceChunk]:
        """
        Re-number source labels sequentially from [SOURCE_1] onwards.
        """
        relabeled: List[EvidenceChunk] = []
        for idx, chunk in enumerate(chunks):
            label = f"[SOURCE_{idx+1}]"
            updated_chunk = chunk.model_copy(
                update={
                    "source_label": label,
                    "rank": idx,
                }
            )
            relabeled.append(updated_chunk)
        return relabeled
