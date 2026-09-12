"""
ip_sakti.confidence.bayesian_confidence — Bayesian Confidence Engine.

Estimates P(Answer is Correct | Retrieved Evidence) using a deterministic
Bayesian log-odds updating model over measurable retrieval & grounding signals:
1. FAISS Cosine Similarity
2. Cross-Encoder Reranker Relevance
3. Citation Grounding
4. Answer-Evidence Consistency
5. Source Agreement & Conflict Detection

Note: Initial weights and prior parameters are configurable engineering heuristics.
They should eventually be calibrated against a labeled validation dataset of
correct/incorrect research answers (e.g. using Platt Scaling or Isotonic Regression).
"""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Any, Sequence

import yaml
from pydantic import BaseModel, Field

from ip_sakti.models.query import CitationRecord, EvidenceChunk

logger = logging.getLogger(__name__)

# Default config path
_CONFIDENCE_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "confidence.yaml"


class BayesianConfidenceResult(BaseModel):
    """Output DTO from the BayesianConfidenceEngine."""

    raw_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Posterior probability score (0.0 to 1.0)."
    )
    confidence_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Confidence percentage (0.0% to 100.0%)."
    )
    confidence_level: str = Field(
        ..., description="Categorical confidence level: 'HIGH', 'MEDIUM', or 'LOW'."
    )
    should_abstain: bool = Field(
        ..., description="True if confidence is below abstention threshold."
    )
    reason: str = Field(
        ..., description="Human-readable explanation of the Bayesian confidence assessment."
    )
    signals: dict[str, float] = Field(
        default_factory=dict,
        description="Individual normalized evidence signals (0.0 to 1.0).",
    )


class BayesianConfidenceEngine:
    """
    Computes deterministic Bayesian confidence P(H | E) where
    H = 'The generated answer is sufficiently supported/correct'.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        prior: float | None = None,
        high_threshold: float | None = None,
        medium_threshold: float | None = None,
        abstain_threshold: float | None = None,
    ) -> None:
        """Initialise engine with YAML config or explicit overrides."""
        cfg_file = Path(config_path) if config_path else _CONFIDENCE_CONFIG_PATH
        cfg = self._load_config(cfg_file)

        conf_cfg = cfg.get("confidence", {})
        thresh_cfg = conf_cfg.get("thresholds", {})
        weights_cfg = conf_cfg.get("evidence_weights", {})

        self.prior = prior if prior is not None else float(conf_cfg.get("prior", 0.50))
        self.max_confidence = float(conf_cfg.get("max_confidence", 0.95))
        self.high_threshold = high_threshold if high_threshold is not None else float(thresh_cfg.get("high", 0.85))
        self.medium_threshold = medium_threshold if medium_threshold is not None else float(thresh_cfg.get("medium", 0.65))
        self.abstain_threshold = abstain_threshold if abstain_threshold is not None else float(thresh_cfg.get("abstain", 0.50))

        self.weights = {
            "cosine_similarity": float(weights_cfg.get("cosine_similarity", 0.30)),
            "reranker_relevance": float(weights_cfg.get("reranker_relevance", 0.30)),
            "citation_grounding": float(weights_cfg.get("citation_grounding", 0.25)),
            "answer_consistency": float(weights_cfg.get("answer_consistency", 0.10)),
            "source_agreement": float(weights_cfg.get("source_agreement", 0.05)),
        }

    def _load_config(self, path: Path) -> dict[str, Any]:
        """Safely load YAML config file."""
        if not path.exists():
            logger.warning(f"Confidence config file not found at {path}. Using defaults.")
            return {}
        try:
            with path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except Exception as err:
            logger.warning(f"Failed to read confidence config: {err}. Using defaults.")
            return {}

    # -------------------------------------------------------------------------
    # Signal Processing & Deterministic Normalization
    # -------------------------------------------------------------------------

    def normalize_cosine_similarity(self, evidence: Sequence[EvidenceChunk]) -> float:
        """
        Normalize FAISS Cosine Similarity to [0.0, 1.0].
        Reuses existing FAISS scores.
        """
        if not evidence:
            return 0.0
        scores = [chunk.faiss_score for chunk in evidence if chunk.faiss_score is not None]
        if not scores:
            return 0.50
        max_score = max(scores)
        # Cosine similarity in FAISS is typically in [0.0, 1.0] for normalized vectors
        return max(0.0, min(1.0, float(max_score)))

    def normalize_reranker_score(self, evidence: Sequence[EvidenceChunk]) -> float:
        """
        Convert Cross-Encoder logit scores to [0.0, 1.0] via sigmoid transform.
        """
        if not evidence:
            return 0.0
        scores = [chunk.rerank_score for chunk in evidence if chunk.rerank_score is not None]
        if not scores:
            return 0.50
        max_score = max(scores)
        # Sigmoid with +4.0 shift (calibrated for MS-MARCO Cross-Encoder logits)
        prob = 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, max_score + 4.0))))
        return max(0.0, min(1.0, float(prob)))

    def calculate_citation_grounding(
        self, citations: Sequence[CitationRecord], evidence: Sequence[EvidenceChunk]
    ) -> float:
        """
        Calculate fraction of grounded answer claims: supported_claims / total_claims.
        If no claims are cited:
          - Default 1.0 if evidence count >= 2
          - Default 0.5 if evidence count < 2
        """
        if citations:
            grounded = sum(1 for c in citations if c.is_grounded)
            return float(grounded / len(citations))
        
        # Safe fallback if answer has no explicit citation tags
        return 0.60 if len(evidence) >= 2 else 0.40

    def calculate_answer_consistency(
        self,
        answer: str,
        evidence: Sequence[EvidenceChunk],
        citations: Sequence[CitationRecord],
    ) -> float:
        """
        Measure textual/semantic overlap between generated answer and evidence chunks.
        """
        if not answer or not evidence:
            return 0.0

        answer_tokens = set(answer.lower().split())
        if not answer_tokens:
            return 0.0

        evidence_tokens: set[str] = set()
        for chunk in evidence:
            if chunk.content:
                evidence_tokens.update(chunk.content.lower().split())

        if not evidence_tokens:
            return 0.0

        # Jaccard / Overlap Ratio of key content words (> 3 chars)
        content_answer_tokens = {t for t in answer_tokens if len(t) > 3}
        if not content_answer_tokens:
            return 0.50

        overlap_count = len(content_answer_tokens.intersection(evidence_tokens))
        overlap_ratio = overlap_count / len(content_answer_tokens)

        # Incorporate citation grounding baseline
        grounding_ratio = self.calculate_citation_grounding(citations, evidence)
        consistency = 0.5 * min(1.0, overlap_ratio * 1.5) + 0.5 * grounding_ratio
        return max(0.0, min(1.0, float(consistency)))

    def calculate_source_agreement(
        self, evidence: Sequence[EvidenceChunk], conflicting: bool = False
    ) -> float:
        """
        Evaluate source agreement across independent retrieved evidence chunks.
        Deduplicates multiple chunks originating from the same parent document.
        """
        if not evidence:
            return 0.0

        if conflicting:
            return 0.20

        # Unique parent source IDs or doc IDs
        unique_sources = set()
        for chunk in evidence:
            s_id = chunk.source_id or chunk.doc_id or chunk.chunk_id
            if s_id:
                unique_sources.add(s_id)

        count = len(unique_sources)
        if count >= 3:
            return 1.0
        elif count == 2:
            return 0.85
        elif count == 1:
            return 0.70
        return 0.50

    # -------------------------------------------------------------------------
    # Core Bayesian Log-Odds Calculation
    # -------------------------------------------------------------------------

    def evaluate_confidence(
        self,
        evidence: Sequence[EvidenceChunk],
        citations: Sequence[CitationRecord],
        answer: str = "",
        conflicting_sources: bool = False,
    ) -> BayesianConfidenceResult:
        """
        Calculate Bayesian posterior probability P(H | E) and classification signals.

        Returns
        -------
        BayesianConfidenceResult
            Complete confidence assessment object.
        """
        evidence_list = list(evidence)
        citation_list = list(citations)

        # 1. Compute Individual Normalized Signals
        sig_cosine = self.normalize_cosine_similarity(evidence_list)
        sig_reranker = self.normalize_reranker_score(evidence_list)
        sig_grounding = self.calculate_citation_grounding(citation_list, evidence_list)
        sig_consistency = self.calculate_answer_consistency(answer, evidence_list, citation_list)
        sig_agreement = self.calculate_source_agreement(evidence_list, conflicting=conflicting_sources)

        signals = {
            "cosine_similarity": round(sig_cosine, 4),
            "reranker_relevance": round(sig_reranker, 4),
            "citation_grounding": round(sig_grounding, 4),
            "answer_consistency": round(sig_consistency, 4),
            "source_agreement": round(sig_agreement, 4),
        }

        # Handle zero evidence case
        if not evidence_list:
            return BayesianConfidenceResult(
                raw_confidence=0.0,
                confidence_percentage=0.0,
                confidence_level="LOW",
                should_abstain=True,
                reason="No evidence chunks retrieved.",
                signals=signals,
            )

        # 2. Bayesian Log-Odds Updating
        eps = 1e-4
        # Prior log-odds L_0 = logit(P(H))
        prior_clamped = max(eps, min(1.0 - eps, self.prior))
        l_0 = math.log(prior_clamped / (1.0 - prior_clamped))

        # Log-likelihood ratio updates from signals (clamped to realistic evidence bounds to prevent saturation)
        delta_l = 0.0
        for sig_name, sig_val in signals.items():
            w = self.weights.get(sig_name, 0.20)
            val_clamped = max(0.12, min(0.88, sig_val))
            # Log-odds contribution relative to neutral 0.5 baseline
            llr = math.log(val_clamped / (1.0 - val_clamped))
            delta_l += w * llr

        # Hard penalty for poor citation grounding (CASE 4 safety requirement)
        if citation_list and sig_grounding < 0.40:
            delta_l -= 1.5  # Strong negative update if claims are ungrounded

        # Hard penalty for conflicting sources (CASE 5 safety requirement)
        if conflicting_sources:
            delta_l -= 1.2

        l_posterior = l_0 + delta_l

        # Convert back from log-odds to probability P(H|E) and apply max_confidence ceiling
        posterior_prob = 1.0 / (1.0 + math.exp(-l_posterior))
        raw_confidence = round(max(0.0, min(self.max_confidence, posterior_prob)), 4)
        confidence_pct = round(raw_confidence * 100.0, 2)

        # 3. Determine Confidence Level & Abstention Status
        if raw_confidence >= self.high_threshold:
            confidence_level = "HIGH"
        elif raw_confidence >= self.medium_threshold:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        should_abstain = raw_confidence < self.abstain_threshold

        # 4. Generate Reason
        if should_abstain:
            reason = (
                f"Confidence score {confidence_pct}% is below "
                f"abstention threshold {self.abstain_threshold * 100:.0f}%."
            )
        else:
            reason = (
                f"{confidence_level} confidence ({confidence_pct}%) "
                f"with grounded evidence and source support."
            )

        # 5. Logging (Development Mode)
        logger.debug(
            "Bayesian Confidence Evaluated",
            extra={
                "prior": self.prior,
                "raw_confidence": raw_confidence,
                "confidence_percentage": confidence_pct,
                "confidence_level": confidence_level,
                "should_abstain": should_abstain,
                "signals": signals,
            },
        )

        return BayesianConfidenceResult(
            raw_confidence=raw_confidence,
            confidence_percentage=confidence_pct,
            confidence_level=confidence_level,
            should_abstain=should_abstain,
            reason=reason,
            signals=signals,
        )
