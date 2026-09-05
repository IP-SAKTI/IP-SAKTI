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

from pydantic import BaseModel, Field, HttpUrl

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
    document_title: str = Field(..., description="Canonical title of the specific document or section")
    publication_date: Optional[str] = Field(default=None, description="Publication date (YYYY-MM-DD)")
    effective_date: Optional[str] = Field(default=None, description="Effective date (YYYY-MM-DD)")
    language: str = Field(default="en", description="ISO 639-1 language code")
    authority_level: str = Field(default="statutory", description="Authority tier: statutory, ministry, institutional, international")
    topic: str = Field(..., description="Domain topic: ip, regulatory, tk_abs")
    checksum: Optional[str] = Field(default=None, description="Version or hash identifier")


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

    def get_source(self, source_id: str) -> AuthorisedSource | None:
        """Retrieve source by source_id."""
        return self._sources.get(source_id)

    def is_authorised_url(self, url: str) -> bool:
        """Return True if URL matches an authorised source domain or URL."""
        if not url:
            return False
        clean_url = url.strip().lower()
        for source in self._sources.values():
            if clean_url.startswith(source.url.lower()):
                return True
        return False
