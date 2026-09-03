"""
ip_sakti.retrieval.fusion — Reciprocal Rank Fusion (RRF) component.

Combines dense FAISS search rankings and sparse BM25 search rankings into a single,
fused candidate ranking using standard Reciprocal Rank Fusion:

    RRF_score(d) = 1 / (k + rank_faiss(d)) + 1 / (k + rank_bm25(d))

Approved per AGENTS.md §3: Hybrid RAG is FAISS (dense) + BM25 (sparse) -> RRF -> Cross-Encoder.
"""

from __future__ import annotations

import logging
from typing import Sequence

from pydantic import BaseModel, Field

from ip_sakti.models.document import KnowledgeDocument
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)


class FusedCandidate(BaseModel):
    """
    A single document chunk after RRF fusion of dense and sparse search results.

    Attributes
    ----------
    chunk :
        The KnowledgeDocument chunk object.
    rrf_score :
        Aggregated Reciprocal Rank Fusion score.
    faiss_score :
        Raw FAISS inner product / cosine similarity score if chunk was in FAISS top-k.
    bm25_score :
        Raw BM25 score if chunk was in BM25 top-k.
    """

    chunk: KnowledgeDocument = Field(..., description="Target document chunk.")
    rrf_score: float = Field(..., description="Reciprocal Rank Fusion score.")
    faiss_score: float | None = Field(default=None, description="FAISS cosine score.")
    bm25_score: float | None = Field(default=None, description="BM25 keyword score.")


class ReciprocalRankFusion:
    """
    Fuses dense and sparse candidate rankings into a unified score.

    Parameters
    ----------
    rrf_k :
        Rank constant k. Defaults to retrieval.rrf_k from config/settings.yaml (default 60).
    """

    def __init__(self, rrf_k: int | None = None) -> None:
        """Initialise RRF with rank constant k."""
        if rrf_k is not None:
            self.rrf_k = rrf_k
        else:
            cfg = get_settings()
            self.rrf_k = int(cfg.get("retrieval", {}).get("rrf_k", 60))

    def fuse(
        self,
        faiss_results: Sequence[tuple[KnowledgeDocument, float]],
        bm25_results: Sequence[tuple[KnowledgeDocument, float]],
    ) -> list[FusedCandidate]:
        """
        Merge FAISS and BM25 search result pairs using RRF scoring.

        Parameters
        ----------
        faiss_results :
            List of (KnowledgeDocument, faiss_score) pairs from dense search.
        bm25_results :
            List of (KnowledgeDocument, bm25_score) pairs from sparse search.

        Returns
        -------
        list[FusedCandidate]
            Fused candidate objects sorted by rrf_score descending.
        """
        if not faiss_results and not bm25_results:
            return []

        # Map doc_id -> {chunk, faiss_score, bm25_score, rrf_score}
        candidates: dict[str, dict] = {}

        # Process FAISS results (1-based rank: rank = index + 1)
        for rank, (chunk, score) in enumerate(faiss_results, start=1):
            doc_id = chunk.doc_id
            rrf_contrib = 1.0 / (self.rrf_k + rank)

            if doc_id not in candidates:
                candidates[doc_id] = {
                    "chunk": chunk,
                    "rrf_score": rrf_contrib,
                    "faiss_score": float(score),
                    "bm25_score": None,
                }
            else:
                candidates[doc_id]["rrf_score"] += rrf_contrib
                candidates[doc_id]["faiss_score"] = float(score)

        # Process BM25 results (1-based rank: rank = index + 1)
        for rank, (chunk, score) in enumerate(bm25_results, start=1):
            doc_id = chunk.doc_id
            rrf_contrib = 1.0 / (self.rrf_k + rank)

            if doc_id not in candidates:
                candidates[doc_id] = {
                    "chunk": chunk,
                    "rrf_score": rrf_contrib,
                    "faiss_score": None,
                    "bm25_score": float(score),
                }
            else:
                candidates[doc_id]["rrf_score"] += rrf_contrib
                candidates[doc_id]["bm25_score"] = float(score)

        fused = [
            FusedCandidate(
                chunk=item["chunk"],
                rrf_score=item["rrf_score"],
                faiss_score=item["faiss_score"],
                bm25_score=item["bm25_score"],
            )
            for item in candidates.values()
        ]

        fused.sort(key=lambda fc: fc.rrf_score, reverse=True)

        logger.debug(
            "RRF fusion completed",
            extra={
                "faiss_count": len(faiss_results),
                "bm25_count": len(bm25_results),
                "fused_count": len(fused),
                "rrf_k": self.rrf_k,
            },
        )
        return fused
