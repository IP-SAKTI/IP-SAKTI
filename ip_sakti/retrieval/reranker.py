"""
ip_sakti.retrieval.reranker — Cross-Encoder evidence reranking component.

Reranks fused candidates produced by RRF using a CrossEncoder model.
Approved per AGENTS.md §5: Preferred cross-encoder model is cross-encoder/ms-marco-MiniLM-L-6-v2.
Model name is read from config/settings.yaml models.cross_encoder_model.
"""

from __future__ import annotations

import logging
from typing import Sequence

from sentence_transformers import CrossEncoder

from ip_sakti.retrieval.exceptions import RetrievalError
from ip_sakti.retrieval.fusion import FusedCandidate
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Reranks candidate document chunks using a CrossEncoder model.

    Parameters
    ----------
    model_name :
        HuggingFace model identifier. Defaults to models.cross_encoder_model
        from config/settings.yaml.
    """

    def __init__(self, model_name: str | None = None) -> None:
        """Initialise reranker with model name."""
        if model_name is not None:
            self.model_name = model_name
        else:
            cfg = get_settings()
            self.model_name = cfg.get("models", {}).get(
                "cross_encoder_model",
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
            )

        self._model: CrossEncoder | None = None
        logger.debug(
            "CrossEncoderReranker initialised",
            extra={"model_name": self.model_name},
        )

    def _get_model(self) -> CrossEncoder:
        """Lazy load the CrossEncoder model on first use."""
        if self._model is None:
            try:
                logger.info(
                    "Loading CrossEncoder model",
                    extra={"model_name": self.model_name},
                )
                self._model = CrossEncoder(self.model_name)
            except Exception as exc:
                raise RetrievalError(
                    f"Failed to load CrossEncoder model {self.model_name!r}: {exc}"
                ) from exc
        return self._model

    def rerank(
        self,
        query: str,
        candidates: Sequence[FusedCandidate],
        top_k: int = 5,
    ) -> list[tuple[FusedCandidate, float]]:
        """
        Rerank fused candidates for a given query text.

        Parameters
        ----------
        query :
            User query text (normalised / translated query).
        candidates :
            List of FusedCandidate objects from RRF fusion.
        top_k :
            Number of top reranked candidates to return.

        Returns
        -------
        list[tuple[FusedCandidate, float]]
            List of (candidate, cross_encoder_score) pairs sorted by score descending.
        """
        if not candidates or top_k <= 0:
            return []

        stripped_query = query.strip()
        if not stripped_query:
            logger.warning("Empty query passed to CrossEncoderReranker.")
            return []

        pairs = [[stripped_query, cand.chunk.content] for cand in candidates]
        model = self._get_model()

        try:
            scores = model.predict(pairs, show_progress_bar=False)
        except Exception as exc:
            raise RetrievalError(f"CrossEncoder prediction failed: {exc}") from exc

        # Pair candidates with scores
        scored_candidates: list[tuple[FusedCandidate, float]] = [
            (cand, float(score)) for cand, score in zip(candidates, scores)
        ]

        scored_candidates.sort(key=lambda item: item[1], reverse=True)

        selected = scored_candidates[:top_k]

        logger.debug(
            "CrossEncoder reranking completed",
            extra={
                "input_candidates": len(candidates),
                "selected_candidates": len(selected),
            },
        )
        return selected
