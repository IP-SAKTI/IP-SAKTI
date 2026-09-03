"""
tests/test_retrieval/test_fusion.py

Unit tests for ip_sakti.retrieval.fusion.ReciprocalRankFusion.
"""

from __future__ import annotations

import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.retrieval.fusion import FusedCandidate, ReciprocalRankFusion


@pytest.fixture()
def sample_chunks() -> list[KnowledgeDocument]:
    meta = DocumentMetadata(source_id="wipo", source_name="WIPO")
    return [
        KnowledgeDocument(doc_id="chunk_A", title="Doc A", content="Content A", metadata=meta),
        KnowledgeDocument(doc_id="chunk_B", title="Doc B", content="Content B", metadata=meta),
        KnowledgeDocument(doc_id="chunk_C", title="Doc C", content="Content C", metadata=meta),
    ]


class TestReciprocalRankFusion:
    def test_rrf_scoring_math(self, sample_chunks: list[KnowledgeDocument]) -> None:
        chunk_a, chunk_b, chunk_c = sample_chunks

        # FAISS ranking: A (rank 1), B (rank 2)
        faiss_res = [(chunk_a, 0.9), (chunk_b, 0.7)]
        # BM25 ranking: B (rank 1), C (rank 2)
        bm25_res = [(chunk_b, 12.5), (chunk_c, 5.0)]

        rrf = ReciprocalRankFusion(rrf_k=60)
        fused = rrf.fuse(faiss_res, bm25_res)

        assert len(fused) == 3
        # Candidate B appears in both FAISS (rank 2) and BM25 (rank 1)
        # Expected score B: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.016129 + 0.016393 = 0.032522
        # Expected score A: 1/(60+1) = 1/61 = 0.016393
        # Expected score C: 1/(60+2) = 1/62 = 0.016129

        top_cand = fused[0]
        assert top_cand.chunk.doc_id == "chunk_B"
        assert top_cand.faiss_score == 0.7
        assert top_cand.bm25_score == 12.5
        assert top_cand.rrf_score == pytest.approx(1.0 / 62 + 1.0 / 61, abs=1e-6)

        second_cand = fused[1]
        assert second_cand.chunk.doc_id == "chunk_A"
        assert second_cand.faiss_score == 0.9
        assert second_cand.bm25_score is None

    def test_empty_results_returns_empty_list(self) -> None:
        rrf = ReciprocalRankFusion(rrf_k=60)
        assert rrf.fuse([], []) == []

    def test_faiss_only_results(self, sample_chunks: list[KnowledgeDocument]) -> None:
        chunk_a = sample_chunks[0]
        faiss_res = [(chunk_a, 0.85)]

        rrf = ReciprocalRankFusion(rrf_k=60)
        fused = rrf.fuse(faiss_res, [])

        assert len(fused) == 1
        assert fused[0].chunk.doc_id == "chunk_A"
        assert fused[0].rrf_score == pytest.approx(1.0 / 61)
