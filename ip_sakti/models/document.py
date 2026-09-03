"""
ip_sakti.models.document — Knowledge document data models.

Defines the data structures for documents stored in the knowledge base
and their provenance metadata, as required by the hybrid RAG pipeline.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class DocumentMetadata(BaseModel):
    """Provenance and administrative metadata for a knowledge base document."""

    source_id: str = Field(
        ...,
        description="Identifier matching a source in config/settings.yaml knowledge_sources.",
        examples=["ip_india", "wipo", "ayush"],
    )
    source_name: str = Field(
        ...,
        description="Human-readable name of the authoritative source.",
        examples=["IP India", "WIPO"],
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Direct URL to the source document or page.",
    )
    authority: Optional[str] = Field(
        default=None,
        description="Name of the issuing authority or organisation.",
    )
    publication_date: Optional[date] = Field(
        default=None,
        description="Publication or last-updated date of the source document.",
    )
    document_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of document, e.g. 'act', 'circular', 'guideline', "
            "'patent', 'research_article', 'database_entry'."
        ),
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Applicable jurisdiction: 'india', 'international', or 'both'.",
    )
    language: str = Field(
        default="en",
        description="ISO 639-1 language code of the source document.",
    )
    permitted_use: bool = Field(
        default=True,
        description=(
            "Whether the document has been confirmed as permissible for inclusion "
            "in the knowledge base under its copyright and access terms."
        ),
    )


class KnowledgeDocument(BaseModel):
    """A single document in the IP-SAKTI knowledge base."""

    doc_id: str = Field(
        ...,
        description="Unique document identifier (UUID or slug).",
    )
    title: str = Field(
        ...,
        description="Title or heading of the document or chunk.",
    )
    content: str = Field(
        ...,
        description="Full text content of the document or chunk.",
    )
    metadata: DocumentMetadata = Field(
        ...,
        description="Provenance and administrative metadata.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description=(
            "Subject tags for filtering, e.g. ['patent', 'ayurveda', 'india', 'tk']."
        ),
    )
    chunk_index: int = Field(
        default=0,
        ge=0,
        description="Zero-based index of this chunk within the parent document.",
    )
    parent_doc_id: Optional[str] = Field(
        default=None,
        description="doc_id of the parent document if this is a chunk.",
    )
