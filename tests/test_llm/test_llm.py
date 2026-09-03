"""
tests/test_llm/test_llm.py

Unit tests for ip_sakti.llm modules: GeminiLLMAdapter, CitationValidator,
ConfidenceAssessor, SafeAbstentionHandler, and AnswerSynthesisService.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ip_sakti.llm.abstention import SafeAbstentionHandler
from ip_sakti.llm.citation_validator import CitationValidator
from ip_sakti.llm.confidence_assessor import ConfidenceAssessor
from ip_sakti.llm.gemini_adapter import GeminiLLMAdapter
from ip_sakti.llm.synthesis_service import AnswerSynthesisService
from ip_sakti.models.query import AgentType, EvidenceChunk, FinalResponse, FormulationCategory, Intent, Jurisdiction, QueryContext


@pytest.fixture()
def sample_context() -> QueryContext:
    return QueryContext(
        query_id=uuid4(),
        raw_query="patent filing rules",
        normalised_query="patent filing rules",
        detected_language="en",
        lang_detect_confidence=1.0,
        translated_query="patent filing rules",
        intent=Intent.IP,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL,
    )


@pytest.fixture()
def sample_evidence() -> list[EvidenceChunk]:
    return [
        EvidenceChunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            content="Patent applications for traditional knowledge are excluded under Section 3(p).",
            source_label="[SOURCE_1]",
            source_name="IP India",
            rerank_score=0.90,
        ),
        EvidenceChunk(
            chunk_id="chunk-2",
            doc_id="doc-2",
            content="Applicants must file Form 1 with full specification.",
            source_label="[SOURCE_2]",
            source_name="IP India",
            rerank_score=0.85,
        ),
    ]


class TestGeminiLLMAdapter:
    def test_generate_answer_fallback(self, sample_context: QueryContext, sample_evidence: list[EvidenceChunk]) -> None:
        adapter = GeminiLLMAdapter(model_name="test-model")
        answer = adapter.generate_answer(sample_context, sample_evidence)
        assert isinstance(answer, str)
        assert "[SOURCE_1]" in answer or "IP India" in answer


class TestCitationValidator:
    def test_validate_citations(self, sample_evidence: list[EvidenceChunk]) -> None:
        validator = CitationValidator()
        answer = "Patent applications for traditional knowledge are excluded [SOURCE_1]."

        records = validator.validate_citations(answer, sample_evidence)
        assert len(records) == 1
        assert records[0].source_label == "[SOURCE_1]"
        assert records[0].is_grounded is True


class TestConfidenceAssessor:
    def test_assess_confidence_high(self, sample_evidence: list[EvidenceChunk]) -> None:
        assessor = ConfidenceAssessor(threshold=0.5, min_evidence_chunks=2)
        res = assessor.assess_confidence(sample_evidence, [])
        assert res.score >= 0.5
        assert res.below_threshold is False

    def test_assess_confidence_empty_evidence(self) -> None:
        assessor = ConfidenceAssessor()
        res = assessor.assess_confidence([], [])
        assert res.score == 0.0
        assert res.below_threshold is True


class TestSafeAbstentionHandler:
    def test_handle_abstention(self, tmp_db_path: Path) -> None:
        from ip_sakti.utils.db import DatabaseManager
        db = DatabaseManager(db_path=tmp_db_path)
        db.initialise()
        handler = SafeAbstentionHandler(db_manager=db)
        qid = uuid4()
        resp = handler.handle_abstention(qid, "Insufficient evidence", AgentType.IP_AGENT)

        assert isinstance(resp, FinalResponse)
        assert resp.is_abstention is True
        assert resp.query_id == qid
        assert resp.disclaimer != ""


class TestAnswerSynthesisService:
    def test_synthesize_high_confidence(self, sample_context: QueryContext, sample_evidence: list[EvidenceChunk]) -> None:
        service = AnswerSynthesisService()
        resp = service.synthesize(sample_context, sample_evidence, AgentType.IP_AGENT)

        assert isinstance(resp, FinalResponse)
        assert resp.is_abstention is False
        assert len(resp.evidence) == 2

    def test_synthesize_empty_evidence_triggers_abstention(self, sample_context: QueryContext) -> None:
        service = AnswerSynthesisService()
        resp = service.synthesize(sample_context, [], AgentType.IP_AGENT)

        assert isinstance(resp, FinalResponse)
        assert resp.is_abstention is True
