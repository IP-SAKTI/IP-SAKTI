"""
ip_sakti.retrieval.web_search — Real Live Web Research Provider & Normalization Engine.

Provides WebSearchProvider abstraction, real live web search capabilities
(via SerpAPI, Tavily, or public DuckDuckGo search), domain authority tiering,
strict prompt injection neutralization, and normalization into EvidenceChunk models.
"""

from __future__ import annotations

import html
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from ip_sakti.models.query import EvidenceChunk

logger = logging.getLogger(__name__)

# Prompt injection neutralization regexes
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"ignore\s+(?:all\s+)?system\s+(?:prompts?|instructions?|messages?)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\b", re.IGNORECASE),
    re.compile(r"new\s+instructions?:", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+must", re.IGNORECASE),
]


def sanitize_web_snippet(text: str, max_chars: int = 1200) -> str:
    """
    Sanitize untrusted external web text.

    Defangs prompt injection attempts and truncates content to safe lengths.
    """
    if not text:
        return ""

    cleaned = html.unescape(text)

    # Defang injection instructions so they are parsed strictly as plain text quotes
    for pat in _INJECTION_PATTERNS:
        cleaned = pat.sub("[EXTERNAL_TEXT_BLOCKED]", cleaned)

    # Strip excess whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) > max_chars:
        words = cleaned[:max_chars].rsplit(" ", 1)[0]
        cleaned = (words if words else cleaned[:max_chars]) + "..."

    return cleaned


def determine_authority_tier(url: Optional[str]) -> int:
    """
    Classify domain authority into Tiers 1, 2, or 3.

    Tier 1: IP India, GoI, AYUSH, CDSCO, WIPO, EPO, USPTO
    Tier 2: PubMed, PMC, peer-reviewed journals, universities (.edu, .ac.in)
    Tier 3: Professional publications, law firms, news, general web
    """
    if not url:
        return 3

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Tier 1: Official government & patent authorities
    tier1_domains = [
        "ipindia.gov.in",
        "ipindiaonline.gov.in",
        "ayush.gov.in",
        "cdsco.gov.in",
        "wipo.int",
        "epo.org",
        "uspto.gov",
        "nbaindia.org",
        "patents.google.com",
    ]
    if any(domain.endswith(t1) or domain == t1 for t1 in tier1_domains) or domain.endswith(".gov.in") or domain.endswith(".nic.in"):
        return 1

    # Tier 2: PubMed, PMC, peer-reviewed journals, academia
    tier2_domains = [
        "ncbi.nlm.nih.gov",
        "pubmed.ncbi.nlm.nih.gov",
        "sciencedirect.com",
        "nature.com",
        "springer.com",
        "tandfonline.com",
        "frontiersin.org",
        "biomedcentral.com",
    ]
    if any(domain.endswith(t2) or domain == t2 for t2 in tier2_domains) or domain.endswith(".edu") or domain.endswith(".ac.in"):
        return 2

    # Tier 3: Everything else
    return 3


class WebSearchProvider(ABC):
    """
    Abstract interface for live web search providers.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        source_types: Optional[List[str]] = None,
        max_results: int = 8,
    ) -> List[EvidenceChunk]:
        """
        Execute search and return normalized EvidenceChunk instances.
        """
        pass


class RealWebSearchProvider(WebSearchProvider):
    """
    Production-ready Web Search Provider supporting SerpAPI, Tavily, and DuckDuckGo fallback.
    """

    def __init__(
        self,
        serpapi_key: Optional[str] = None,
        tavily_key: Optional[str] = None,
        timeout: float = 8.0,
    ) -> None:
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY", "")
        self.tavily_key = tavily_key or os.getenv("TAVILY_API_KEY", "")
        self.timeout = timeout

    def search(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        source_types: Optional[List[str]] = None,
        max_results: int = 8,
    ) -> List[EvidenceChunk]:
        """
        Execute live web query against external providers in priority order.
        """
        if not query or not query.strip():
            return []

        # 1. Try SerpAPI if configured
        if self.serpapi_key:
            try:
                results = self._search_serpapi(query, max_results=max_results)
                if results:
                    return results
            except Exception as exc:
                logger.warning(f"SerpAPI search failed: {exc}. Trying next provider.")

        # 2. Try Tavily if configured
        if self.tavily_key:
            try:
                results = self._search_tavily(query, max_results=max_results)
                if results:
                    return results
            except Exception as exc:
                logger.warning(f"Tavily search failed: {exc}. Trying next provider.")

        # 3. Use DuckDuckGo Instant/HTML search (Zero-API-key open web provider)
        try:
            return self._search_duckduckgo(query, max_results=max_results)
        except Exception as exc:
            logger.warning(f"DuckDuckGo live web search failed: {exc}")
            return []

    def _search_serpapi(self, query: str, max_results: int) -> List[EvidenceChunk]:
        """Query Google via SerpAPI."""
        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "engine": "google",
            "num": max_results,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                raise RuntimeError(f"SerpAPI returned HTTP {resp.status_code}")
            data = resp.json()
            organic = data.get("organic_results", [])
            return self._normalize_raw_results(organic, provider_type="serpapi")

    def _search_tavily(self, query: str, max_results: int) -> List[EvidenceChunk]:
        """Query Tavily Search API."""
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": max_results,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Tavily returned HTTP {resp.status_code}")
            data = resp.json()
            results = data.get("results", [])
            return self._normalize_raw_results(results, provider_type="tavily")

    def _search_duckduckgo(self, query: str, max_results: int) -> List[EvidenceChunk]:
        """
        Query DuckDuckGo Instant Answer API / HTML Lite without requiring API keys.
        """
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) IP-SAKTI-Researcher/1.0"}
        with httpx.Client(timeout=self.timeout, headers=headers) as client:
            items = []
            try:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    # AbstractText
                    if data.get("AbstractText"):
                        items.append({
                            "title": data.get("Heading") or query,
                            "link": data.get("AbstractURL") or "https://duckduckgo.com",
                            "snippet": data.get("AbstractText"),
                            "source": data.get("AbstractSource"),
                        })

                    # RelatedTopics
                    for topic in data.get("RelatedTopics", []):
                        if isinstance(topic, dict) and topic.get("Text"):
                            items.append({
                                "title": topic.get("Text", "")[:60],
                                "link": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", ""),
                                "source": "DuckDuckGo Topic",
                            })
                        elif isinstance(topic, dict) and "Topics" in topic:
                            for sub in topic["Topics"]:
                                if sub.get("Text"):
                                    items.append({
                                        "title": sub.get("Text", "")[:60],
                                        "link": sub.get("FirstURL", ""),
                                        "snippet": sub.get("Text", ""),
                                        "source": "DuckDuckGo SubTopic",
                                    })
            except Exception as exc:
                logger.debug(f"DuckDuckGo Instant API did not return results: {exc}")

            # Fallback to DuckDuckGo HTML Lite when instant answers are empty
            if not items:
                try:
                    html_url = "https://html.duckduckgo.com/html/"
                    resp_html = client.post(html_url, data={"q": query})
                    if resp_html.status_code == 200:
                        raw_html = resp_html.text
                        snippet_matches = re.findall(r'class="result__snippet[^"]*">(.*?)</a>', raw_html, re.DOTALL)
                        title_matches = re.findall(r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', raw_html, re.DOTALL)
                        for idx in range(min(len(snippet_matches), len(title_matches), max_results)):
                            link, raw_title = title_matches[idx]
                            clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                            clean_snip = re.sub(r'<[^>]+>', '', snippet_matches[idx]).strip()
                            if clean_snip:
                                items.append({
                                    "title": clean_title or query,
                                    "link": link,
                                    "snippet": clean_snip,
                                    "source": "DuckDuckGo Web",
                                })
                except Exception as h_exc:
                    logger.debug(f"DuckDuckGo HTML fallback failed: {h_exc}")

            return self._normalize_raw_results(items[:max_results], provider_type="duckduckgo")

    def _normalize_raw_results(self, raw_items: List[Dict[str, Any]], provider_type: str) -> List[EvidenceChunk]:
        """
        Transform raw provider items into standardized EvidenceChunk models.
        """
        evidence_list: List[EvidenceChunk] = []

        for idx, item in enumerate(raw_items):
            title = item.get("title") or "Web Search Evidence"
            url = item.get("link") or item.get("url") or ""
            raw_snippet = item.get("snippet") or item.get("content") or item.get("body") or ""
            source_name = item.get("source") or (urlparse(url).netloc if url else "Web Search")

            cleaned_snippet = sanitize_web_snippet(raw_snippet)
            if not cleaned_snippet:
                continue

            tier = determine_authority_tier(url)
            # Base relevance scoring influenced by tier
            base_score = 0.90 if tier == 1 else (0.75 if tier == 2 else 0.55)

            chunk_id = f"live_web_{idx}_{uuid4().hex[:8]}"
            source_id = f"SRC_LIVE_{idx+1}"

            evidence = EvidenceChunk(
                chunk_id=chunk_id,
                doc_id=f"doc_live_{idx+1}",
                source_id=source_id,
                content=cleaned_snippet,
                source_label=f"[SOURCE_{idx+1}]",
                source_name=source_name,
                source_url=url,
                title=title,
                authority=source_name,
                document_type="live_web_source",
                jurisdiction="india" if ("ipindia" in url or "ayush" in url) else "international",
                rerank_score=base_score,
                rank=idx,
            )
            evidence_list.append(evidence)

        return evidence_list
