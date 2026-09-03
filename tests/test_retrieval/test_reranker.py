"""
tests/test_retrieval/test_reranker.py

Unit tests for ip_sakti.retrieval.reranker.CrossEncoderReranker.
Uses mocking to avoid downloading real CrossEncoder weights during testing.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.retrieval.exceptions import RetrievalError
from ip_sakti.retrieval.fusion import FusedCandidate
from ip_sakti.retrieval.reranker import CrossEncoderReranker


@pytest.fixture()
def sample_fused_candidates() -> list[FusedCandidate]:
    meta = DocumentMetadata(source_id="ip_india", source_name="IP India")
    c1 = KnowledgeDocument(
        doc_id="cand_1", title="Doc 1", content="Patent filing guidelines Section 3p", metadata=meta
    )
    c2 = KnowledgeDocument(
        doc_id="cand_2", title="Doc 2", content="General Trademark rules", metadata=meta
    )
    return [
        FusedCandidate(chunk=c1, rrf_score=0.03),
        FusedCandidate(chunk=c2, rrf_score=0.02),
    ]


class TestCrossEncoderReranker:
    @patch("ip_sakti.retrieval.reranker.CrossEncoder")
    def test_rerank_orders_by_score_descending(
        self, mock_ce_cls: MagicMock, sample_fused_candidates: list[FusedCandidate]
    ) -> None:
        mock_model = MagicMock()
        # Pretend pair 2 (cand_2) gets 0.95 and pair 1 (cand_1) gets 0.10
        mock_model.predict.return_value = [0.10, 0.95]
        mock_ce_cls.return_value = mock_model

        reranker = CrossEncoderReranker(model_name="dummy-ce")
        reranked = reranker.rerank("ayush query", sample_fused_candidates, top_k=2)

        assert len(reranked) == 2
        top_cand, score = reranked[0]
        assert top_cand.chunk.doc_id == "cand_2"
        assert score == 0.95

    def test_empty_candidates_returns_empty_list(self) -> None:
        reranker = CrossEncoderReranker()
        assert reranker.rerank("query", [], top_k=5) == []

    def test_empty_query_returns_empty_list(
        self, sample_fused_candidates: list[FusedCandidate]
    ) -> None:
        reranker = CrossEncoderReranker()
        assert reranker.rerank("   ", sample_fused_candidates, top_k=5) == []

    @patch("ip_sakti.retrieval.reranker.CrossEncoder")
    def test_prediction_error_raises_retrieval_error(
        self, mock_ce_cls: MagicMock, sample_fused_candidates: list[FusedCandidate]
    ) -> None:
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("GPU out of memory")
        mock_ce_cls.return_value = mock_model

        reranker = CrossEncoderReranker(model_name="dummy-ce")
        with pytest.raises(RetrievalError, match="CrossEncoder prediction failed"):
            reranker.rerank("query", sample_fused_candidates, top_k=5)
