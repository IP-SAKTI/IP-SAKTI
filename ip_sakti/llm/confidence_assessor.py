"""
ip_sakti.llm.confidence_assessor — Confidence assessment component.

Approved per AGENTS.md §7: Confidence assessment must be computed and returned
as part of every response object. Score below threshold triggers safe abstention.
"""

from __future__ import annotations

import logging
import math
from typing import Sequence

from ip_sakti.models.query import CitationRecord, ConfidenceResult, EvidenceChunk
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)


class ConfidenceAssessor:
    """
    Computes numerical confidence score and evaluates threshold compliance.

    Safety principle:
    Good citation coverage alone is NOT sufficient. The retrieved evidence
    must also be relevant to the user's query.
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

        # Hard safety threshold for retrieval relevance.
        #
        # If the retrieved evidence has an extremely low rerank score,
        # the evidence is probably unrelated to the user's question.
        #
        # In that situation the system must abstain even if the LLM
        # successfully cites the irrelevant evidence.
        self.retrieval_safety_threshold = 0.10

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
            Retrieved and reranked evidence chunks.

        citations :
            Citation records produced by CitationValidator.

        Returns
        -------
        ConfidenceResult
            Confidence score, coverage metrics, and below_threshold flag.
        """

        # ------------------------------------------------------------------
        # 1. Check whether evidence exists
        # ------------------------------------------------------------------

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

        # ------------------------------------------------------------------
        # 2. Calculate average retrieval relevance
        # ------------------------------------------------------------------

        rerank_scores = [
            chunk.rerank_score
            for chunk in evidence
            if chunk.rerank_score is not None
        ]

        if rerank_scores:
            raw_avg = sum(rerank_scores) / len(rerank_scores)

            # Convert cross-encoder logits to a 0–1 value.
            avg_rerank = 1.0 / (
                1.0
                + math.exp(
                    -max(-10.0, min(10.0, raw_avg))
                )
            )
        else:
            # If rerank scores are unavailable, use a neutral value.
            avg_rerank = 0.5

        # ------------------------------------------------------------------
        # 3. Calculate citation coverage
        # ------------------------------------------------------------------

        if citations:
            grounded_count = sum(
                1
                for citation in citations
                if citation.is_grounded
            )

            citation_coverage = grounded_count / len(citations)

        else:
            citation_coverage = (
                1.0
                if evidence_count >= self.min_evidence_chunks
                else 0.5
            )

        # ------------------------------------------------------------------
        # 4. Calculate evidence-count factor
        # ------------------------------------------------------------------

        count_factor = min(
            1.0,
            evidence_count / self.min_evidence_chunks,
        )

        # ------------------------------------------------------------------
        # 5. Calculate overall confidence score
        # ------------------------------------------------------------------

        score = float(
            0.4 * avg_rerank
            + 0.4 * citation_coverage
            + 0.2 * count_factor
        )

        score = round(
            max(0.0, min(1.0, score)),
            4,
        )

        # ------------------------------------------------------------------
        # 6. IMPORTANT SAFETY CHECK
        # ------------------------------------------------------------------
        #
        # A response can have perfect citation coverage while still being
        # based on irrelevant documents.
        #
        # Example:
        #
        # User asks:
        # "What is the patent fee in Antarctica?"
        #
        # Retrieved documents:
        # "Indian Ayurvedic manufacturing licence"
        #
        # The LLM may correctly cite those documents, but they do not
        # answer the user's question.
        #
        # Therefore extremely poor retrieval relevance forces abstention.

        retrieval_unsafe = (
            avg_rerank < self.retrieval_safety_threshold
        )

        # ------------------------------------------------------------------
        # 7. Determine whether the answer is safe
        # ------------------------------------------------------------------

        below_threshold = (
            score < self.threshold
            or evidence_count < self.min_evidence_chunks
            or retrieval_unsafe
        )

        # ------------------------------------------------------------------
        # 8. Explain why abstention happened
        # ------------------------------------------------------------------

        if below_threshold:

            if evidence_count < self.min_evidence_chunks:

                reason = (
                    f"Insufficient evidence chunks "
                    f"({evidence_count} < required "
                    f"{self.min_evidence_chunks})."
                )

            elif retrieval_unsafe:

                reason = (
                    f"Retrieved evidence has insufficient relevance "
                    f"(rerank score {avg_rerank:.4f} < "
                    f"safety threshold "
                    f"{self.retrieval_safety_threshold:.2f})."
                )

            else:

                reason = (
                    f"Confidence score {score:.2f} is below "
                    f"threshold {self.threshold:.2f}."
                )

        else:

            reason = (
                f"High confidence ({score:.2f} >= "
                f"{self.threshold:.2f}) with sufficient evidence."
            )

        # ------------------------------------------------------------------
        # 9. Logging
        # ------------------------------------------------------------------

        logger.debug(
            "Assessed response confidence",
            extra={
                "score": score,
                "below_threshold": below_threshold,
                "retrieval_unsafe": retrieval_unsafe,
                "avg_rerank_score": avg_rerank,
                "citation_coverage": citation_coverage,
                "evidence_count": evidence_count,
                "reason": reason,
            },
        )

        # ------------------------------------------------------------------
        # 10. Return result
        # ------------------------------------------------------------------

        return ConfidenceResult(
            score=score,
            evidence_count=evidence_count,
            citation_coverage=round(
                citation_coverage,
                4,
            ),
            avg_rerank_score=round(
                avg_rerank,
                4,
            ),
            below_threshold=below_threshold,
            reason=reason,
        )