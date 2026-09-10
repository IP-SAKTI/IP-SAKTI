"""
ip_sakti.llm.confidence_assessor — Confidence assessment component.

Uses BayesianConfidenceEngine to compute deterministic P(Answer is Correct | Evidence).
Score below abstention threshold triggers safe abstention.
"""

from __future__ import annotations

import logging
from typing import Sequence

from ip_sakti.confidence import BayesianConfidenceEngine
from ip_sakti.models.query import CitationRecord, ConfidenceResult, EvidenceChunk
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)


class ConfidenceAssessor:
    """
    Computes Bayesian confidence score and evaluates safety threshold.
    """

    def __init__(
        self,
        threshold: float | None = None,
        min_evidence_chunks: int | None = None,
        bayesian_engine: BayesianConfidenceEngine | None = None,
    ) -> None:
        """Initialise ConfidenceAssessor using config or explicit overrides."""

        cfg = get_settings()
        safety_cfg = cfg.get("safety", {})

        self.threshold = (
            threshold
            if threshold is not None
            else float(safety_cfg.get("confidence_threshold", 0.5))
        )

        self.min_evidence_chunks = (
            min_evidence_chunks
            if min_evidence_chunks is not None
            else int(safety_cfg.get("min_evidence_chunks", 2))
        )

        self.bayesian_engine = bayesian_engine or BayesianConfidenceEngine(
            abstain_threshold=self.threshold
        )

    def assess_confidence(
        self,
        evidence: Sequence[EvidenceChunk],
        citations: Sequence[CitationRecord],
        answer: str = "",
        conflicting_sources: bool = False,
    ) -> ConfidenceResult:
        """
        Calculate confidence score via BayesianConfidenceEngine and evaluate safety threshold.

        Parameters
        ----------
        evidence :
            Retrieved and reranked evidence chunks.
        citations :
            Citation records produced by CitationValidator.
        answer :
            Generated answer text.
        conflicting_sources :
            Whether source conflict was detected.

        Returns
        -------
        ConfidenceResult
            Confidence score, coverage metrics, signals, and below_threshold flag.
        """
        evidence_count = len(evidence)

        if evidence_count == 0:
            return ConfidenceResult(
                score=0.0,
                evidence_count=0,
                citation_coverage=0.0,
                avg_rerank_score=0.0,
                below_threshold=True,
                reason="No evidence chunks retrieved.",
                confidence_percentage=0.0,
                confidence_level="LOW",
                signals={
                    "cosine_similarity": 0.0,
                    "reranker_relevance": 0.0,
                    "citation_grounding": 0.0,
                    "answer_consistency": 0.0,
                    "source_agreement": 0.0,
                },
            )

        # Execute Bayesian Confidence Engine
        bayes_res = self.bayesian_engine.evaluate_confidence(
            evidence=evidence,
            citations=citations,
            answer=answer,
            conflicting_sources=conflicting_sources,
        )

        citation_coverage = bayes_res.signals.get("citation_grounding", 0.0)
        avg_rerank = bayes_res.signals.get("reranker_relevance", 0.0)

        below_threshold = bayes_res.should_abstain or (evidence_count < self.min_evidence_chunks and bayes_res.raw_confidence < 0.70)

        logger.debug(
            "Assessed Bayesian response confidence",
            extra={
                "score": bayes_res.raw_confidence,
                "confidence_pct": bayes_res.confidence_percentage,
                "confidence_level": bayes_res.confidence_level,
                "below_threshold": below_threshold,
                "reason": bayes_res.reason,
                "signals": bayes_res.signals,
            },
        )

        return ConfidenceResult(
            score=bayes_res.raw_confidence,
            evidence_count=evidence_count,
            citation_coverage=round(citation_coverage, 4),
            avg_rerank_score=round(avg_rerank, 4),
            below_threshold=below_threshold,
            reason=bayes_res.reason,
            confidence_percentage=bayes_res.confidence_percentage,
            confidence_level=bayes_res.confidence_level,
            signals=bayes_res.signals,
        )