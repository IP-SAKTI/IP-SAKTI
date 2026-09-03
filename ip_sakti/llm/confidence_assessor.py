"""
ip_sakti.llm.confidence_assessor — Confidence assessment component.

Approved per AGENTS.md §7: Confidence assessment must be computed and returned
as part of every response object. Score below threshold triggers safe abstention.
"""

from __future__ import annotations

import logging
from typing import Sequence

from ip_sakti.models.query import CitationRecord, ConfidenceResult, EvidenceChunk
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)


class ConfidenceAssessor:
    """
    Computes numerical confidence score and evaluates threshold compliance.
    """

    def __init__(
        self,
        threshold: float | None = None,
        min_evidence_chunks: int | None = None,
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

    def assess_confidence(
        self,
        evidence: Sequence[EvidenceChunk],
        citations: Sequence[CitationRecord],
    ) -> ConfidenceResult:
        """
        Calculate confidence score and evaluate safety threshold.

        Parameters
        ----------
        evidence :
            Retrieved EvidenceChunk list.
        citations :
            CitationRecord list from CitationValidator.

        Returns
        -------
        ConfidenceResult
            Confidence score (0.0–1.0), coverage metrics, and below_threshold flag.
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
            )

        # Average rerank score (normalised to 0..1 if raw logits)
        rerank_scores = [c.rerank_score for c in evidence if c.rerank_score is not None]
        if rerank_scores:
            raw_avg = sum(rerank_scores) / len(rerank_scores)
            # Map logit to roughly 0..1
            avg_rerank = max(0.0, min(1.0, (raw_avg + 5.0) / 10.0))
        else:
            avg_rerank = 0.5

        # Citation coverage
        if citations:
            grounded_count = sum(1 for c in citations if c.is_grounded)
            citation_coverage = grounded_count / len(citations)
        else:
            citation_coverage = 1.0 if evidence_count >= self.min_evidence_chunks else 0.5

        # Evidence count factor
        count_factor = min(1.0, evidence_count / self.min_evidence_chunks)

        # Weighted aggregate score
        score = float(0.4 * avg_rerank + 0.4 * citation_coverage + 0.2 * count_factor)
        score = round(max(0.0, min(1.0, score)), 4)

        below_threshold = score < self.threshold or evidence_count < self.min_evidence_chunks

        if below_threshold:
            if evidence_count < self.min_evidence_chunks:
                reason = f"Insufficient evidence chunks ({evidence_count} < required {self.min_evidence_chunks})."
            else:
                reason = f"Confidence score {score:.2f} is below threshold {self.threshold:.2f}."
        else:
            reason = f"High confidence ({score:.2f} >= {self.threshold:.2f}) with sufficient evidence."

        logger.debug(
            "Assessed response confidence",
            extra={"score": score, "below_threshold": below_threshold, "reason": reason},
        )

        return ConfidenceResult(
            score=score,
            evidence_count=evidence_count,
            citation_coverage=round(citation_coverage, 4),
            avg_rerank_score=round(avg_rerank, 4),
            below_threshold=below_threshold,
            reason=reason,
        )
