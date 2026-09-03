"""
tests/test_models.py — Unit tests for ip_sakti.models.

Tests that Pydantic v2 models:
  - accept valid input and construct correctly
  - reject invalid input with ValidationError
  - enum values are valid
  - default values are applied correctly
  - FinalResponse always includes a disclaimer
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from ip_sakti.models import (
    AgentResult,
    AgentType,
    CitationRecord,
    ConfidenceResult,
    EscalationRecord,
    EvidenceChunk,
    FinalResponse,
    FormulationCategory,
    Intent,
    Jurisdiction,
    KnowledgeDocument,
    QueryContext,
    QueryRequest,
)
from ip_sakti.models.document import DocumentMetadata


# =============================================================================
# Enum tests
# =============================================================================


class TestEnums:
    def test_intent_values(self) -> None:
        assert Intent.IP == "ip"
        assert Intent.REGULATORY == "regulatory"
        assert Intent.TK_ABS == "tk_abs"
        assert Intent.AMBIGUOUS == "ambiguous"

    def test_jurisdiction_values(self) -> None:
        assert Jurisdiction.INDIA == "india"
        assert Jurisdiction.INTERNATIONAL == "international"
        assert Jurisdiction.BOTH == "both"
        assert Jurisdiction.UNKNOWN == "unknown"

    def test_formulation_category_values(self) -> None:
        expected = {"classical", "proprietary", "new_drug", "phytopharmaceutical",
                    "nutraceutical", "cosmetic", "unknown"}
        actual = {m.value for m in FormulationCategory}
        assert expected == actual

    def test_agent_type_values(self) -> None:
        expected = {"ip_agent", "regulatory_agent", "tk_abs_agent"}
        actual = {a.value for a in AgentType}
        assert expected == actual


# =============================================================================
# QueryRequest
# =============================================================================


class TestQueryRequest:
    def test_valid_minimal(self) -> None:
        req = QueryRequest(raw_query="What is the patent filing fee in India?")
        assert isinstance(req.query_id, UUID)
        assert req.jurisdiction == Jurisdiction.UNKNOWN
        assert req.formulation_category == FormulationCategory.UNKNOWN

    def test_valid_with_jurisdiction(self) -> None:
        req = QueryRequest(
            raw_query="ABS regulations",
            jurisdiction=Jurisdiction.INDIA,
            formulation_category=FormulationCategory.CLASSICAL,
        )
        assert req.jurisdiction == Jurisdiction.INDIA

    def test_empty_query_rejected(self) -> None:
        with pytest.raises(ValidationError, match="raw_query"):
            QueryRequest(raw_query="")

    def test_query_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(raw_query="x" * 2001)

    def test_invalid_jurisdiction_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(raw_query="test", jurisdiction="mars")  # type: ignore[arg-type]


# =============================================================================
# DocumentMetadata and KnowledgeDocument
# =============================================================================


class TestDocumentMetadata:
    def test_valid_minimal(self) -> None:
        meta = DocumentMetadata(source_id="wipo", source_name="WIPO")
        assert meta.permitted_use is True
        assert meta.language == "en"

    def test_valid_full(self) -> None:
        meta = DocumentMetadata(
            source_id="ip_india",
            source_name="IP India",
            source_url="https://www.ipindia.gov.in",
            authority="CGPDTM",
            publication_date=date(2024, 1, 15),
            document_type="guideline",
            jurisdiction="india",
            language="en",
            permitted_use=True,
        )
        assert meta.publication_date == date(2024, 1, 15)

    def test_missing_source_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DocumentMetadata(source_name="WIPO")  # type: ignore[call-arg]


class TestKnowledgeDocument:
    def test_valid_document(self) -> None:
        meta = DocumentMetadata(source_id="ayush", source_name="Ministry of AYUSH")
        doc = KnowledgeDocument(
            doc_id="doc-001",
            title="AYUSH Guideline on Classical Medicines",
            content="This guideline covers classical Ayurvedic medicines...",
            metadata=meta,
        )
        assert doc.chunk_index == 0
        assert doc.parent_doc_id is None
        assert doc.tags == []

    def test_chunk_index_cannot_be_negative(self) -> None:
        meta = DocumentMetadata(source_id="ayush", source_name="AYUSH")
        with pytest.raises(ValidationError):
            KnowledgeDocument(
                doc_id="doc-002",
                title="Test",
                content="content",
                metadata=meta,
                chunk_index=-1,
            )


# =============================================================================
# EvidenceChunk
# =============================================================================


class TestEvidenceChunk:
    def test_valid_chunk(self) -> None:
        chunk = EvidenceChunk(
            chunk_id="chunk-001",
            doc_id="doc-001",
            content="Patent applications in India must be filed...",
            source_label="[SOURCE_1]",
            source_name="IP India",
        )
        assert chunk.rank == 0
        assert chunk.rerank_score is None

    def test_rank_cannot_be_negative(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceChunk(
                chunk_id="c",
                doc_id="d",
                content="x",
                source_label="[S]",
                source_name="S",
                rank=-1,
            )


# =============================================================================
# CitationRecord
# =============================================================================


class TestCitationRecord:
    def test_grounded_citation(self) -> None:
        rec = CitationRecord(
            claim_snippet="Patent must be filed within 12 months",
            source_label="[SOURCE_1]",
            chunk_id="chunk-001",
            is_grounded=True,
        )
        assert rec.grounding_method == "substring"

    def test_ungrounded_citation(self) -> None:
        rec = CitationRecord(
            claim_snippet="Something unverified",
            source_label="[SOURCE_2]",
            chunk_id="chunk-002",
            is_grounded=False,
        )
        assert rec.is_grounded is False


# =============================================================================
# ConfidenceResult
# =============================================================================


class TestConfidenceResult:
    def test_valid_high_confidence(self) -> None:
        result = ConfidenceResult(
            score=0.85,
            evidence_count=5,
            citation_coverage=0.9,
            avg_rerank_score=0.75,
            below_threshold=False,
            reason="Strong evidence with high coverage.",
        )
        assert result.below_threshold is False

    def test_score_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ConfidenceResult(
                score=1.5,  # invalid — above 1.0
                evidence_count=3,
                citation_coverage=0.8,
                avg_rerank_score=0.6,
                below_threshold=False,
                reason="x",
            )


# =============================================================================
# FinalResponse
# =============================================================================


class TestFinalResponse:
    def test_answer_response(self) -> None:
        qid = uuid4()
        resp = FinalResponse(
            query_id=qid,
            answer="Patent applications in India are governed by...",
            is_abstention=False,
        )
        assert resp.query_id == qid
        assert resp.is_abstention is False
        # Disclaimer must always be present and non-empty
        assert resp.disclaimer
        assert len(resp.disclaimer) > 10

    def test_abstention_response(self) -> None:
        resp = FinalResponse(
            query_id=uuid4(),
            answer="Insufficient evidence to answer this query reliably.",
            is_abstention=True,
        )
        assert resp.is_abstention is True

    def test_disclaimer_always_present(self) -> None:
        """Disclaimer cannot be set to an empty string."""
        # Default disclaimer is always populated by the model
        resp = FinalResponse(query_id=uuid4(), answer="Some answer.")
        assert resp.disclaimer != ""


# =============================================================================
# EscalationRecord
# =============================================================================


class TestEscalationRecord:
    def test_valid_escalation(self) -> None:
        record = EscalationRecord(
            query_id=uuid4(),
            reason="Confidence score 0.2 is below threshold 0.5.",
        )
        assert record.agent_type is None

    def test_escalation_with_agent(self) -> None:
        record = EscalationRecord(
            query_id=uuid4(),
            reason="Insufficient evidence.",
            agent_type=AgentType.IP_AGENT,
        )
        assert record.agent_type == AgentType.IP_AGENT
