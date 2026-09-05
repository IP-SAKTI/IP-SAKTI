"""
tests/test_truncation.py — Tests for answer completeness and citation safety.

Verifies:
  - Answers do not end mid-sentence (truncation detection)
  - Fabricated [SOURCE_99] citations are marked as ungrounded
  - Empty-citation coverage is not 1.0 (no false-perfect confidence)
  - Low-evidence queries still trigger abstention
"""

from __future__ import annotations

import re
from uuid import uuid4

import pytest

from ip_sakti.llm.citation_validator import CitationValidator
from ip_sakti.llm.confidence_assessor import ConfidenceAssessor
from ip_sakti.models.query import (
    CitationRecord,
    EvidenceChunk,
    FormulationCategory,
    Intent,
    Jurisdiction,
    QueryContext,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chunk(
    idx: int = 1,
    content: str = "Rule 158-B requires Form 24D for manufacturing Ayurvedic drugs.",
    rerank_score: float = 2.5,
) -> EvidenceChunk:
    """Create a minimal EvidenceChunk for testing."""
    return EvidenceChunk(
        chunk_id=f"chunk_{idx}",
        doc_id=f"doc_{idx}",
        content=content,
        source_label=f"[SOURCE_{idx}]",
        source_name="Test Source",
        rerank_score=rerank_score,
    )


def _make_context(query: str = "What form is needed?") -> QueryContext:
    return QueryContext(
        query_id=uuid4(),
        raw_query=query,
        normalised_query=query.lower(),
        detected_language="en",
        lang_detect_confidence=1.0,
        translated_query=query,
        intent=Intent.REGULATORY,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL,
    )


def _is_truncated(text: str) -> bool:
    """
    Return True if the answer appears to end abruptly.

    Heuristics:
    - Ends without terminal punctuation (. ? ! : ;)
    - Last word is a conjunction / preposition / article suggesting a cut
    - Text ends mid-word (no space before end)
    """
    if not text:
        return True
    stripped = text.strip()
    if not stripped:
        return True

    # Check terminal punctuation
    terminal_chars = {".", "?", "!", ":", ";", ")", "]", '"', "'"}
    if stripped[-1] not in terminal_chars:
        # Tolerate short one-word answers (e.g. "Unknown")
        if len(stripped.split()) > 3:
            return True

    # Check if last word is a dangling connective
    last_word = stripped.split()[-1].lower().rstrip(".,;:?!")
    dangling = {"and", "or", "but", "the", "a", "an", "in", "of", "for",
                "to", "with", "by", "at", "from", "on", "rule", "under",
                "which", "that", "this", "these", "those", "is", "are",
                "was", "were", "has", "have", "may", "shall", "must"}
    if last_word in dangling and len(stripped.split()) > 5:
        return True

    return False


# ---------------------------------------------------------------------------
# Test: truncation detection helper
# ---------------------------------------------------------------------------

class TestTruncationDetector:
    """Verify the _is_truncated heuristic works correctly."""

    def test_complete_sentence_not_truncated(self) -> None:
        complete = "Rule 158-B requires Form 24D [SOURCE_1]. This is a complete answer."
        assert not _is_truncated(complete)

    def test_sentence_ending_mid_word_is_truncated(self) -> None:
        truncated = "The licensing steps under Rule 158-B for manufacturing Ayurveda, Siddha, and Unani (ASU) drugs involve several mandatory requirements and procedures. Rule"
        assert _is_truncated(truncated)

    def test_sentence_ending_with_connective_is_truncated(self) -> None:
        truncated = "The applicant must submit Form 24D and"
        assert _is_truncated(truncated)

    def test_empty_string_is_truncated(self) -> None:
        assert _is_truncated("")

    def test_short_valid_answer_not_truncated(self) -> None:
        assert not _is_truncated("Form 24D.")


# ---------------------------------------------------------------------------
# Test: Citation validator rejects fabricated source labels
# ---------------------------------------------------------------------------

class TestCitationValidatorFabricatedSources:
    """Fabricated [SOURCE_99] should be rejected (is_grounded=False)."""

    def test_fabricated_source_label_is_not_grounded(self) -> None:
        validator = CitationValidator()

        # Answer references [SOURCE_99] which is not in evidence
        answer = "The applicant must pay a fee [SOURCE_99]."

        # Only [SOURCE_1] is in evidence
        evidence = [_make_chunk(idx=1)]

        records = validator.validate_citations(answer, evidence)

        assert len(records) == 1
        assert records[0].source_label == "[SOURCE_99]"
        assert records[0].is_grounded is False

    def test_real_source_label_is_grounded(self) -> None:
        validator = CitationValidator()

        answer = "Form 24D is required to apply for an Ayurvedic manufacturing licence [SOURCE_1]."
        evidence = [_make_chunk(
            idx=1,
            content="Form 24D is the application form for a manufacturing licence for Ayurvedic drugs.",
        )]

        records = validator.validate_citations(answer, evidence)

        assert len(records) == 1
        assert records[0].source_label == "[SOURCE_1]"
        assert records[0].is_grounded is True

    def test_no_citations_returns_empty_records(self) -> None:
        validator = CitationValidator()

        # Answer has no [SOURCE_X] labels at all
        answer = "Form 24D is required."
        evidence = [_make_chunk(idx=1)]

        records = validator.validate_citations(answer, evidence)
        assert records == []


# ---------------------------------------------------------------------------
# Test: ConfidenceAssessor citation coverage edge cases
# ---------------------------------------------------------------------------

class TestConfidenceAssessorCoverage:
    """Citation coverage must not default to 1.0 when no citations exist."""

    def test_empty_citations_do_not_give_perfect_coverage(self) -> None:
        assessor = ConfidenceAssessor()
        evidence = [_make_chunk(idx=1), _make_chunk(idx=2)]

        result = assessor.assess_confidence(evidence=evidence, citations=[])

        # citation_coverage must not be 1.0 when no citations in answer
        assert result.citation_coverage < 1.0, (
            f"Expected citation_coverage < 1.0 for uncited answer, got {result.citation_coverage}"
        )

    def test_fully_grounded_citations_give_high_coverage(self) -> None:
        assessor = ConfidenceAssessor()
        evidence = [_make_chunk(idx=1), _make_chunk(idx=2)]

        citations = [
            CitationRecord(
                claim_snippet="Form 24D is required [SOURCE_1].",
                source_label="[SOURCE_1]",
                chunk_id="chunk_1",
                is_grounded=True,
                grounding_method="substring",
            ),
            CitationRecord(
                claim_snippet="Rule 158-B specifies requirements [SOURCE_2].",
                source_label="[SOURCE_2]",
                chunk_id="chunk_2",
                is_grounded=True,
                grounding_method="substring",
            ),
        ]

        result = assessor.assess_confidence(evidence=evidence, citations=citations)
        assert result.citation_coverage == 1.0

    def test_all_ungrounded_citations_give_zero_coverage(self) -> None:
        assessor = ConfidenceAssessor()
        evidence = [_make_chunk(idx=1)]

        citations = [
            CitationRecord(
                claim_snippet="Completely fabricated claim [SOURCE_99].",
                source_label="[SOURCE_99]",
                chunk_id="unknown",
                is_grounded=False,
                grounding_method="substring",
            ),
        ]

        result = assessor.assess_confidence(evidence=evidence, citations=citations)
        assert result.citation_coverage == 0.0

    def test_no_evidence_gives_abstention(self) -> None:
        assessor = ConfidenceAssessor()

        result = assessor.assess_confidence(evidence=[], citations=[])

        assert result.below_threshold is True
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# Test: ConfidenceAssessor retrieval safety threshold
# ---------------------------------------------------------------------------

class TestConfidenceAssessorRetrievalSafety:
    """Very low rerank scores must trigger abstention even if citation coverage is good."""

    def test_low_rerank_score_triggers_abstention(self) -> None:
        assessor = ConfidenceAssessor()

        # Chunks with very low rerank scores (irrelevant evidence)
        evidence = [
            _make_chunk(idx=1, rerank_score=-10.0),  # logit → sigmoid ≈ 0.0000
            _make_chunk(idx=2, rerank_score=-9.0),
        ]

        citations = [
            CitationRecord(
                claim_snippet="Some claim [SOURCE_1].",
                source_label="[SOURCE_1]",
                chunk_id="chunk_1",
                is_grounded=True,
                grounding_method="substring",
            ),
        ]

        result = assessor.assess_confidence(evidence=evidence, citations=citations)

        # Even with good citation coverage, irrelevant evidence → abstention
        assert result.below_threshold is True
