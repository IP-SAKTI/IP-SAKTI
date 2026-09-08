"""
ip_sakti.retrieval.patent_search — Specialized Patent Search Provider Abstraction.

Encapsulates official patent search endpoints (EPO OPS, WIPO PATENTSCOPE, Google Patents)
separate from generic web search. Provides graceful fallback when API credentials
are unconfigured or external services are unreachable.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from ip_sakti.models.query import EvidenceChunk
from ip_sakti.retrieval.web_search import sanitize_web_snippet

logger = logging.getLogger(__name__)


class PatentSearchProvider(ABC):
    """
    Abstract interface for specialized patent retrieval providers.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        max_results: int = 5,
    ) -> List[EvidenceChunk]:
        """
        Query patent databases and return standardized EvidenceChunk objects.
        """
        pass


class RealPatentSearchProvider(PatentSearchProvider):
    """
    Production-grade patent search provider supporting official APIs with safe fallback.
    """

    def __init__(
        self,
        patent_api_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        timeout: float = 8.0,
    ) -> None:
        self.api_key = patent_api_key or os.getenv("PATENT_API_KEY", "")
        self.endpoint_url = endpoint_url or os.getenv("PATENT_ENDPOINT_URL", "")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Check if patent API credentials and endpoint are present."""
        return bool(self.api_key or self.endpoint_url)

    def search(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        max_results: int = 5,
    ) -> List[EvidenceChunk]:
        """
        Search official patent endpoints if configured; otherwise gracefully return empty list.
        """
        if not query or not query.strip():
            return []

        if not self.is_configured:
            logger.info("Patent API key not configured; patent search safely defaulting to web/internal RAG.")
            return []

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
            params = {"q": query, "limit": max_results}
            if jurisdiction:
                params["jurisdiction"] = jurisdiction

            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self.endpoint_url, headers=headers, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Patent search endpoint returned HTTP {resp.status_code}")
                    return []
                data = resp.json()
                items = data.get("patents") or data.get("results") or []
                return self._normalize_patent_results(items)

        except Exception as exc:
            logger.warning(f"Patent search provider encountered error: {exc}. Safely continuing.")
            return []

    def _normalize_patent_results(self, items: List[Dict[str, Any]]) -> List[EvidenceChunk]:
        """
        Transform raw patent items into standardized EvidenceChunk models.
        """
        evidence_list: List[EvidenceChunk] = []

        for idx, item in enumerate(items):
            patent_number = item.get("patent_number") or item.get("id") or f"PAT-{idx+1}"
            title = item.get("title") or f"Patent Application {patent_number}"
            abstract = item.get("abstract") or item.get("summary") or item.get("snippet") or ""
            url = item.get("url") or f"https://patents.google.com/patent/{patent_number}"
            office = item.get("office") or "Official Patent Office"

            cleaned_abstract = sanitize_web_snippet(abstract)
            if not cleaned_abstract:
                continue

            chunk_id = f"live_patent_{idx}_{uuid4().hex[:8]}"
            source_id = f"SRC_PAT_{patent_number}"

            evidence = EvidenceChunk(
                chunk_id=chunk_id,
                doc_id=f"doc_patent_{patent_number}",
                source_id=source_id,
                content=cleaned_abstract,
                source_label=f"[PATENT_{idx+1}]",
                source_name=f"Patent {patent_number} ({office})",
                source_url=url,
                title=title,
                authority=office,
                document_type="patent",
                jurisdiction="india" if (patent_number.startswith("IN") or "india" in office.lower()) else "international",
                rerank_score=0.92,  # Official patent document Tier 1
                rank=idx,
            )
            evidence_list.append(evidence)

        return evidence_list
