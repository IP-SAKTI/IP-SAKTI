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
    cosine_similarity: Optional[float] = Field(
        default=None, description="Actual cosine similarity score from FAISS dense vector search."
    )
    confidence_score: Optional[float] = Field(
        default=None, description="Bayesian raw confidence probability (0.0 to 1.0)."
    )
    confidence_percentage: Optional[float] = Field(
        default=None, description="Bayesian confidence percentage (0.0 to 100.0%)."
    )
    confidence_level: Optional[str] = Field(
        default=None, description="Confidence level: 'HIGH', 'MEDIUM', or 'LOW'."
    )
    confidence_should_abstain: Optional[bool] = Field(
        default=None, description="True if confidence is below abstention threshold."
    )
    confidence_signals: Optional[dict[str, float]] = Field(
        default_factory=dict, description="Bayesian evidence signals."
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
    detected_language: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code detected from user query.",
    )
    original_query: Optional[str] = Field(
        default=None,
        description="Original user query before normalization.",
    )
    normalized_english_query: Optional[str] = Field(
        default=None,
        description="Query normalized to English for retrieval.",
    )
    answer_language: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code of the generated answer.",
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


class MagicLinkRequest(BaseModel):
    """Request payload for triggering a Supabase Magic Link email."""

    email: str = Field(..., description="Email address to send the magic link to.")
    redirect_to: str = Field(
        default="http://localhost:3000/auth/callback",
        description="Frontend callback URL Supabase redirects to after link click.",
    )


class MagicLinkResponse(BaseModel):
    """Response after sending a magic link."""

    status: str = Field(default="sent", description="'sent' on success.")
    message: str = Field(default="Magic link sent. Check your email.")


class AuthResponse(BaseModel):
    user: dict
    token: Optional[str] = None
    message: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    user_id: Optional[str] = None
    fullName: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    bio: Optional[str] = None
    avatarUrl: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    fullName: str
    email: str
    organization: str = "IP-SAKTI"
    role: str = "Researcher"
    bio: str = ""
    avatarUrl: str = ""



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

