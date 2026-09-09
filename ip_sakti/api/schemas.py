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
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID of active conversation session.",
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Recent conversation history turns for session context.",
    )
    search_mode: str = Field(
        default="hybrid",
        description="Retrieval search mode: 'internal', 'live', or 'hybrid'.",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional authenticated user ID.",
    )


class APIQueryResponse(BaseModel):
    """HTTP response payload for /query endpoint."""

    query_id: UUID = Field(..., description="Unique query execution UUID.")
    answer: str = Field(..., description="Generated answer or safe abstention text.")
    is_abstention: bool = Field(..., description="True if system safely declined to answer.")
    confidence: Optional[float] = Field(
        default=None, description="Canonical confidence score between 0.0 and 1.0."
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
    search_mode: str = Field(
        default="hybrid",
        description="Search mode executed.",
    )
    live_research_metadata: Optional[dict] = Field(
        default=None,
        description="Live web/patent research execution metadata.",
    )


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: Optional[str] = None
    terms_accepted: bool = True


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user: dict
    token: str
    message: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    user_id: Optional[str] = None
    fullName: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    bio: Optional[str] = None
    avatarUrl: Optional[str] = None


class ContactRequest(BaseModel):
    name: str
    email: str
    subject: str
    message: str
    user_id: Optional[str] = None


class ContactResponse(BaseModel):
    status: str = "success"
    message: str = "Inquiry received successfully."


class SaveHistoryRequest(BaseModel):
    id: str
    title: str
    query: Optional[str] = None
    user_id: Optional[str] = None
    response: Optional[dict] = None

