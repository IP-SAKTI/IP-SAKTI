"""
ip_sakti.retrieval.sources — Authorised Knowledge Source Registry.

Provides models and registry services for managing first-class government and
statutory knowledge sources approved for inclusion in the IP-SAKTI knowledge base.

Approved per AGENTS.md §11 & MVP Spec: Grounded answers must come strictly from
authorised and permitted sources.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Sequence

from pydantic import BaseModel, Field, HttpUrl, field_validator

logger = logging.getLogger(__name__)

_DEFAULT_SOURCES_PATH = Path(__file__).parent.parent.parent / "config" / "sources.json"


class AuthorisedSource(BaseModel):
    """Metadata schema for a first-class authorised knowledge source."""

    source_id: str = Field(..., description="Unique slug for the source")
    title: str = Field(..., description="Full official title of the legal/regulatory source")
    organisation: str = Field(..., description="Issuing government body or authority")
    source_type: str = Field(..., description="Type of document: act, rule, regulation, guideline, database_entry")
    jurisdiction: str = Field(..., description="Applicable jurisdiction: india, international, both")
    url: str = Field(..., description="Authorised government URL")
    canonical_url: Optional[str] = Field(default=None, description="Canonical official resource page URL")
    archive_url: Optional[str] = Field(default=None, description="Wayback Machine archived snapshot URL (https://web.archive.org/...)")
    document_title: str = Field(..., description="Canonical title of the specific document or section")
    publication_date: Optional[str] = Field(default=None, description="Publication date (YYYY-MM-DD)")
    effective_date: Optional[str] = Field(default=None, description="Effective date (YYYY-MM-DD)")
    language: str = Field(default="en", description="ISO 639-1 language code")
    authority_level: str = Field(default="statutory", description="Authority tier: statutory, ministry, institutional, international")
    topic: str = Field(..., description="Domain topic: ip, regulatory, tk_abs")
    checksum: Optional[str] = Field(default=None, description="Version or hash identifier")

    @field_validator("archive_url")
    @classmethod
    def validate_archive_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        clean = v.strip()
        if not clean.startswith("https://web.archive.org/"):
            raise ValueError("archive_url must begin with 'https://web.archive.org/'")
        return clean



_ALIAS_MAP: dict[str, str] = {
    "doc_patents_act_3p": "ip_india_patents_act_3p",
    "patents_act_3p": "ip_india_patents_act_3p",
    "doc_ayush_rule_158b": "ayush_rule_158b",
    "doc_ayush_form_24d": "ayush_form_24d",
    "doc_biodiversity_act_2002": "biodiversity_act_2002",
    "doc_nba_abs_regulations_2014": "nba_abs_regulations_2014",
    "doc_tkdl_wipo_policy": "tkdl_wipo_policy",
    "doc_ccras_ayush_pharmacopoeia": "ccras_ayush_pharmacopoeia",
    "doc_cdsco_drugs_rules_1945": "cdsco_drugs_rules_1945",
}


class SourceRegistry:
    """
    Central registry for loading, querying, and validating authorised knowledge sources.
    """

    def __init__(self, registry_path: Path | str | None = None) -> None:
        """Initialise registry from json file path or default config location."""
        self.path = Path(registry_path) if registry_path else _DEFAULT_SOURCES_PATH
        self._sources: dict[str, AuthorisedSource] = {}
        self.load()

    def load(self) -> None:
        """Load authorised sources from disk."""
        if not self.path.exists():
            logger.warning(f"Authorised source registry file not found at {self.path}")
            return

        try:
            with self.path.open("r", encoding="utf-8") as fh:
                raw_data = json.load(fh)
            
            loaded = [AuthorisedSource.model_validate(item) for item in raw_data]
            self._sources = {s.source_id: s for s in loaded}
            logger.info("Loaded authorised source registry", extra={"count": len(self._sources)})
        except Exception as exc:
            logger.error(f"Failed to load authorised source registry from {self.path}: {exc}")

    def list_sources(self) -> list[AuthorisedSource]:
        """Return all registered sources."""
        return list(self._sources.values())

    def resolve_source_id(self, source_id: str) -> str | None:
        """
        Deterministically resolve any given source_id or alias to a canonical
        registered source_id from sources.json.
        """
        if not source_id:
            return None
        clean_id = source_id.strip().lower()

        # 1. Exact match on registered source_id
        if clean_id in self._sources:
            return clean_id

        # 2. Check explicit alias map
        if clean_id in _ALIAS_MAP and _ALIAS_MAP[clean_id] in self._sources:
            return _ALIAS_MAP[clean_id]

        # 3. Check stripped 'doc_' prefix
        if clean_id.startswith("doc_"):
            stripped = clean_id[4:]
            if stripped in self._sources:
                return stripped
            if stripped in _ALIAS_MAP and _ALIAS_MAP[stripped] in self._sources:
                return _ALIAS_MAP[stripped]

        # 4. Suffix/substring matching against registered keys
        for key in self._sources:
            if key.endswith(clean_id) or clean_id.endswith(key):
                return key

        return None

    def get_source(self, source_id: str) -> AuthorisedSource | None:
        """Retrieve AuthorisedSource model by source_id or alias."""
        resolved_id = self.resolve_source_id(source_id)
        if resolved_id:
            return self._sources.get(resolved_id)
        return None

    def get_knowledge_document(self, source_id: str) -> dict | None:
        """Find local knowledge JSON document matching the source ID or doc_id."""
        knowledge_dir = self.path.parent.parent / "data" / "knowledge"
        if not knowledge_dir.exists():
            return None

        resolved_id = self.resolve_source_id(source_id) or source_id.strip().lower()

        candidates = [
            f"{source_id}.json",
            f"doc_{source_id}.json",
            f"{resolved_id}.json",
            f"doc_{resolved_id}.json",
        ]

        for fname in candidates:
            filepath = knowledge_dir / fname
            if filepath.is_file():
                try:
                    with filepath.open("r", encoding="utf-8") as fh:
                        return json.load(fh)
                except Exception as exc:
                    logger.error(f"Error reading knowledge file {filepath}: {exc}")

        for filepath in knowledge_dir.glob("*.json"):
            try:
                with filepath.open("r", encoding="utf-8") as fh:
                    doc = json.load(fh)
                doc_id = str(doc.get("doc_id", "")).lower()
                meta_source_id = str(doc.get("metadata", {}).get("source_id", "")).lower()
                if doc_id in (source_id.lower(), resolved_id) or meta_source_id in (source_id.lower(), resolved_id):
                    return doc
            except Exception:
                continue

        return None

    def get_local_document_file(self, source_id: str) -> Path | None:
        """Locate local PDF or document file in data/documents/ matching source_id."""
        docs_dir = (self.path.parent.parent / "data" / "documents").resolve()
        if not docs_dir.exists():
            return None

        resolved_id = self.resolve_source_id(source_id) or source_id.strip().lower()

        candidates = [
            f"{source_id}.pdf",
            f"doc_{source_id}.pdf",
            f"{resolved_id}.pdf",
            f"doc_{resolved_id}.pdf",
        ]

        for fname in candidates:
            filepath = (docs_dir / fname).resolve()
            # Security check: ensure path traversal cannot escape docs_dir
            try:
                filepath.relative_to(docs_dir)
            except ValueError:
                continue

            if filepath.is_file():
                return filepath

        return None

    def get_source_viewer_data(self, source_id: str) -> dict | None:
        """Assemble structured data for the IP-SAKTI Local Source Document Viewer."""
        resolved_id = self.resolve_source_id(source_id)
        if not resolved_id:
            return None

        source_meta = self._sources.get(resolved_id)
        if not source_meta:
            return None

        kb_doc = self.get_knowledge_document(source_id) or self.get_knowledge_document(resolved_id)

        local_available = False
        content = ""
        title = source_meta.title
        authority = source_meta.organisation
        document_type = source_meta.source_type

        if kb_doc:
            local_available = True
            content = kb_doc.get("content", "")
            if kb_doc.get("title"):
                title = kb_doc.get("title")
            meta = kb_doc.get("metadata", {})
            if meta.get("authority"):
                authority = meta.get("authority")
            if meta.get("document_type"):
                document_type = meta.get("document_type")

        archive_url = source_meta.archive_url
        is_valid_archive = bool(archive_url and archive_url.startswith("https://web.archive.org/"))

        return {
            "source_id": resolved_id,
            "title": title,
            "organisation": source_meta.organisation,
            "authority": authority,
            "document_type": document_type,
            "jurisdiction": source_meta.jurisdiction,
            "official_url": source_meta.url,
            "archive_url": archive_url,
            "is_authorised_url": self.is_authorised_url(source_meta.url),
            "is_valid_archive_url": is_valid_archive,
            "content": content,
            "local_available": local_available,
            "publication_date": source_meta.publication_date,
        }

    def is_authorised_url(self, url: str) -> bool:
        """Return True if URL matches an authorised source domain or URL."""
        if not url:
            return False
        clean_url = url.strip().lower()
        from urllib.parse import urlparse
        parsed = urlparse(clean_url)
        netloc = parsed.netloc

        for source in self._sources.values():
            s_url = source.url.lower()
            if clean_url.startswith(s_url):
                return True
            s_netloc = urlparse(s_url).netloc
            if netloc and s_netloc and (netloc == s_netloc or netloc.endswith("." + s_netloc)):
                return True
            if source.canonical_url:
                c_netloc = urlparse(source.canonical_url.lower()).netloc
                if netloc and c_netloc and (netloc == c_netloc or netloc.endswith("." + c_netloc)):
                    return True
        return False

    def validate_urls(self, check_network: bool = False) -> list[dict]:
        """
        Validate all registered external source URLs for formatting, host correctness,
        obsolete paths (e.g. www.ipindia.gov.in host mismatch), and optionally connectivity.
        """
        from urllib.parse import urlparse
        results = []

        for source_id, source in self._sources.items():
            entry = {
                "source_id": source_id,
                "url": source.url,
                "canonical_url": source.canonical_url,
                "is_valid": True,
                "warnings": [],
                "errors": [],
            }

            # 1. Structural syntax check
            try:
                parsed = urlparse(source.url)
                if parsed.scheme not in ("http", "https") or not parsed.netloc:
                    entry["is_valid"] = False
                    entry["errors"].append("Malformed URL: scheme must be http/https and netloc non-empty")
            except Exception as exc:
                entry["is_valid"] = False
                entry["errors"].append(f"Failed to parse URL: {exc}")

            # 2. Check obsolete www.ipindia.gov.in host
            if "www.ipindia.gov.in" in source.url.lower():
                entry["is_valid"] = False
                entry["errors"].append("Obsolete www.ipindia.gov.in host (SSL certificate mismatch error). Use ipindia.gov.in")

            # 3. Check localhost / private host
            if "localhost" in source.url.lower() or "127.0.0.1" in source.url:
                entry["is_valid"] = False
                entry["errors"].append("URL uses localhost or private IP instead of official domain")

            # 4. Optional network connectivity check
            if check_network and entry["is_valid"]:
                import urllib.request
                import urllib.error
                import ssl
                ctx = ssl.create_default_context()
                req = urllib.request.Request(
                    source.url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) IP-SAKTI-Auditor/1.0'}
                )
                try:
                    with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                        entry["network_status"] = response.status
                        entry["final_url"] = response.url
                except urllib.error.HTTPError as he:
                    entry["network_status"] = he.code
                    entry["warnings"].append(f"HTTP Server returned status {he.code}")
                except urllib.error.URLError as ue:
                    entry["warnings"].append(f"Network check failed (temporary server issue): {ue.reason}")
                except Exception as ex:
                    entry["warnings"].append(f"Network error: {ex}")

            results.append(entry)

        return results




