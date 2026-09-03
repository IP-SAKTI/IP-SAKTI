"""
ip_sakti.models.query — Core request/response data models.

These Pydantic v2 models are shared across every layer of the architecture:
Streamlit UI → FastAPI → Orchestrator → Agents → RAG → LLM → Response.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Enumerations
# =============================================================================


class Intent(str, Enum):
    """Classified user intent, determined by the Orchestrator."""

    IP = "ip"
    REGULATORY = "regulatory"
    TK_ABS = "tk_abs"
    AMBIGUOUS = "ambiguous"


class Jurisdiction(str, Enum):
    """Jurisdiction scope for the query."""

    INDIA = "india"
    INTERNATIONAL = "international"
    BOTH = "both"
    UNKNOWN = "unknown"


class FormulationCategory(str, Enum):
    """Ayurvedic or related product/formulation category."""

    CLASSICAL = "classical"
    PROPRIETARY = "proprietary"
    NEW_DRUG = "new_drug"
    PHYTOPHARMACEUTICAL = "phytopharmaceutical"
    NUTRACEUTICAL = "nutraceutical"
    COSMETIC = "cosmetic"
    UNKNOWN = "unknown"


class AgentType(str, Enum):
    """Specialist agent identifiers."""

    IP_AGENT = "ip_agent"
    REGULATORY_AGENT = "regulatory_agent"
    TK_ABS_AGENT = "tk_abs_agent"


# =============================================================================
# Request
# =============================================================================


class QueryRequest(BaseModel):
    """Incoming query from the user via the Streamlit UI or API."""

    query_id: UUID = Field(
        default_factory=uuid4,
        description="Auto-generated unique identifier for this query session.",
    )
    raw_query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's original query text, in any supported language.",
    )
    jurisdiction: Jurisdiction = Field(
        default=Jurisdiction.UNKNOWN,
        description="Jurisdiction explicitly selected by the user.",
    )
    formulation_category: FormulationCategory = Field(
        default=FormulationCategory.UNKNOWN,
        description="Formulation category explicitly selected or implied by the user.",
    )
    user_language: Optional[str] = Field(
        default=None,
        description=(
            "ISO 639-1 language code supplied by the user. "
            "If None, language detection is used."
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the query was submitted.",
    )


# =============================================================================
# Intermediate context
# =============================================================================


class QueryContext(BaseModel):
    """
    Enriched query context assembled by the Orchestrator after classification.

    Passed to the Rule Engine and Agent Router.
    """

    query_id: UUID = Field(..., description="Matches the originating QueryRequest.")
    raw_query: str = Field(..., description="Original query text.")
    normalised_query: str = Field(
        ...,
        description="Query after normalisation (lowercase, unicode NFC, etc.).",
    )
    detected_language: str = Field(
        ...,
        description="ISO 639-1 code of the detected query language.",
    )
    lang_detect_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from the language detector (0.0–1.0).",
    )
    translated_query: str = Field(
        ...,
        description="Query translated to English for retrieval and processing.",
    )
    intent: Intent = Field(
        ...,
        description="Classified intent of the query.",
    )
    jurisdiction: Jurisdiction = Field(
        ...,
        description="Resolved jurisdiction (from user input or classification).",
    )
    formulation_category: FormulationCategory = Field(
        ...,
        description="Resolved formulation category.",
    )
    routing_flags: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary flags set by the Rule Engine for downstream use.",
    )
    document_filters: list[str] = Field(
        default_factory=list,
        description="Document tag filters to apply during retrieval.",
    )
    agents_to_invoke: list[AgentType] = Field(
        default_factory=list,
        description="Ordered list of specialist agents selected by the Agent Router.",
    )


# =============================================================================
# Retrieval
# =============================================================================


class EvidenceChunk(BaseModel):
    """A single retrieved and reranked evidence passage."""

    chunk_id: str = Field(..., description="Unique identifier of the document chunk.")
    doc_id: str = Field(..., description="Parent document identifier.")
    content: str = Field(..., description="Text of the evidence chunk.")
    source_label: str = Field(
        ...,
        description="Citation label used in the answer, e.g. '[SOURCE_1]'.",
    )
    source_name: str = Field(..., description="Human-readable source name.")
    source_url: Optional[str] = Field(
        default=None,
        description="URL of the source document.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Title or heading of the document or chunk.",
    )
    authority: Optional[str] = Field(
        default=None,
        description="Issuing authority or organisation name.",
    )
    publication_date: Optional[date] = Field(
        default=None,
        description="Publication date of the source document.",
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Type of document, e.g. 'act', 'guideline', 'patent'.",
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Applicable jurisdiction.",
    )
    faiss_score: Optional[float] = Field(
        default=None,
        description="Cosine similarity score from FAISS dense search.",
    )
    bm25_score: Optional[float] = Field(
        default=None,
        description="BM25 score from sparse search.",
    )
    rrf_score: Optional[float] = Field(
        default=None,
        description="Reciprocal Rank Fusion score after merging FAISS and BM25.",
    )
    rerank_score: Optional[float] = Field(
        default=None,
        description="Cross-encoder reranking score (higher = more relevant).",
    )
    rank: int = Field(
        default=0,
        ge=0,
        description="Final rank after reranking (0 = most relevant).",
    )


# =============================================================================
# Validation & confidence
# =============================================================================


class CitationRecord(BaseModel):
    """
    Records whether a specific claim in the generated answer
    is grounded in a retrieved evidence chunk.
    """

    claim_snippet: str = Field(
        ...,
        description="Short excerpt from the generated answer containing the claim.",
    )
    source_label: str = Field(
        ...,
        description="Citation label that the answer attributed to this claim.",
    )
    chunk_id: str = Field(
        ...,
        description="ID of the evidence chunk that was expected to ground the claim.",
    )
    is_grounded: bool = Field(
        ...,
        description="True if the claim is supported by the cited evidence chunk.",
    )
    grounding_method: str = Field(
        default="substring",
        description="Method used for grounding check: 'substring' or 'semantic'.",
    )


class ConfidenceResult(BaseModel):
    """Composite confidence assessment for a generated answer."""

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0.0 = no confidence, 1.0 = full confidence).",
    )
    evidence_count: int = Field(
        ...,
        ge=0,
        description="Number of evidence chunks used.",
    )
    citation_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of answer claims that are grounded in retrieved evidence.",
    )
    avg_rerank_score: float = Field(
        ...,
        description="Average cross-encoder reranking score of the evidence chunks.",
    )
    below_threshold: bool = Field(
        ...,
        description="True if the confidence score is below the configured threshold.",
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation of the confidence assessment.",
    )


# =============================================================================
# Agent output
# =============================================================================


class AgentResult(BaseModel):
    """Output produced by a single specialist agent."""

    agent_type: AgentType = Field(..., description="Which agent produced this result.")
    query_id: UUID = Field(..., description="Matches the originating query.")
    evidence: list[EvidenceChunk] = Field(
        default_factory=list,
        description="Retrieved and reranked evidence chunks.",
    )
    raw_answer: str = Field(
        default="",
        description="Raw answer text generated by the LLM before validation.",
    )
    citations: list[CitationRecord] = Field(
        default_factory=list,
        description="Citation validation records.",
    )
    confidence: Optional[ConfidenceResult] = Field(
        default=None,
        description="Confidence assessment for this agent's answer.",
    )
    escalate: bool = Field(
        default=False,
        description="True if this result triggers safe abstention / escalation.",
    )


# =============================================================================
# Final response
# =============================================================================


class EscalationRecord(BaseModel):
    """Logged record of a safe-abstention escalation event."""

    query_id: UUID = Field(..., description="ID of the query that triggered escalation.")
    reason: str = Field(..., description="Reason for escalation.")
    escalated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_type: Optional[AgentType] = Field(
        default=None,
        description="Agent that triggered escalation, if applicable.",
    )


class FinalResponse(BaseModel):
    """
    The complete, user-facing response returned by the system.

    Includes the answer or abstention message, all citations,
    confidence data, and the disclaimer.
    """

    query_id: UUID = Field(..., description="Matches the originating QueryRequest.")
    answer: str = Field(
        ...,
        description=(
            "The final answer text to present to the user, with inline citations. "
            "If abstaining, this contains the safe-abstention message."
        ),
    )
    is_abstention: bool = Field(
        default=False,
        description="True if the system abstained rather than providing an answer.",
    )
    citations: list[CitationRecord] = Field(
        default_factory=list,
        description="All citation validation records for this response.",
    )
    evidence: list[EvidenceChunk] = Field(
        default_factory=list,
        description="All evidence chunks used to generate this response.",
    )
    confidence: Optional[ConfidenceResult] = Field(
        default=None,
        description="Aggregated confidence assessment.",
    )
    detected_language: str = Field(
        default="en",
        description="Language in which the query was submitted.",
    )
    response_language: str = Field(
        default="en",
        description="Language in which the answer is returned.",
    )
    disclaimer: str = Field(
        default=(
            "This response is for informational purposes only and does not "
            "constitute legal, regulatory, or IP advice. Consult a qualified "
            "professional for guidance specific to your situation."
        ),
        description="Mandatory disclaimer appended to every response.",
    )
    agents_invoked: list[AgentType] = Field(
        default_factory=list,
        description="List of specialist agents that contributed to this response.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the response was generated.",
    )
