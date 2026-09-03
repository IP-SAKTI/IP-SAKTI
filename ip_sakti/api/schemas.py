"""
ip_sakti.api.schemas — Pydantic v2 HTTP Request and Response DTOs.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ip_sakti.models.query import CitationRecord, ConfidenceResult, EvidenceChunk


class HealthResponse(BaseModel):
    """Healthcheck response model."""

    status: str = "ok"
    service: str = "ip-sakti-sahayak"
    version: str = "0.1.0"


class APIQueryRequest(BaseModel):
    """HTTP request payload for /query endpoint."""

    raw_query: str = Field(
        ...,
        description="User query in English or an Indic language.",
        examples=["What are the Section 3(p) patent requirements for Ayurvedic drugs in India?"],
    )
    jurisdiction: str = Field(
        default="unknown",
        description="Target jurisdiction (india, international, both, or unknown).",
    )
    formulation_category: str = Field(
        default="unknown",
        description="Formulation category (classical, proprietary, new_drug, etc.).",
    )
    user_language: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code if explicitly specified by user.",
    )


class APIQueryResponse(BaseModel):
    """HTTP response payload for /query endpoint."""

    query_id: UUID = Field(..., description="Unique query execution UUID.")
    answer: str = Field(..., description="Generated answer or safe abstention text.")
    is_abstention: bool = Field(..., description="True if system safely declined to answer.")
    confidence: Optional[ConfidenceResult] = Field(
        default=None, description="Confidence assessment metrics."
    )
    evidence: list[EvidenceChunk] = Field(
        default_factory=list, description="Source-grounded evidence chunks."
    )
    citations: list[CitationRecord] = Field(
        default_factory=list, description="Citation validation records."
    )
    agents_invoked: list[str] = Field(
        default_factory=list, description="List of specialist agent identifiers invoked."
    )
    disclaimer: str = Field(..., description="Legal and regulatory informational disclaimer.")
