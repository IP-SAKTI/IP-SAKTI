"""
tests/test_retrieval/test_pipeline.py

End-to-end unit tests for ip_sakti.retrieval.pipeline.HybridRAGPipeline.
Uses synthetic document fixtures and mock embedding/reranking components
for fast, isolated execution.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.models.query import EvidenceChunk
from ip_sakti.retrieval.bm25_store import BM25SparseStore
from ip_sakti.retrieval.chunker import DocumentChunker
from ip_sakti.retrieval.embeddings import EmbeddingGenerator
from ip_sakti.retrieval.faiss_store import FAISSVectorStore
from ip_sakti.retrieval.fusion import ReciprocalRankFusion
from ip_sakti.retrieval.pipeline import HybridRAGPipeline
from ip_sakti.retrieval.reranker import CrossEncoderReranker


@pytest.fixture()
def synthetic_knowledge_base() -> list[KnowledgeDocument]:
    meta_ip = DocumentMetadata(
        source_id="ip_india",
        source_name="IP India Patent Office",
        source_url="https://www.ipindia.gov.in/guidelines",
        authority="CGPDTM",
        publication_date=date(2024, 1, 15),
        document_type="guideline",
        jurisdiction="india",
    )

    meta_ayush = DocumentMetadata(
        source_id="ayush",
        source_name="Ministry of AYUSH",
        source_url="https://www.ayush.gov.in/rules",
        authority="Ministry of AYUSH",
        publication_date=date(2023, 6, 10),
        document_type="act",
        jurisdiction="india",
    )

    return [
        KnowledgeDocument(
            doc_id="doc-pat-001",
            title="Section 3(p) Patent Exclusion for Traditional Knowledge",
            content=(
                "Section 3(p) of the Indian Patents Act 1970 excludes inventions which are in effect "
                "traditional knowledge or an aggregation or duplication of known properties of traditionally "
                "known components from patentability."
            ),
            metadata=meta_ip,
            tags=["patent", "tk", "section3p"],
        ),
        KnowledgeDocument(
            doc_id="doc-abs-002",
            title="National Biodiversity Authority ABS Compliance",
            content=(
                "Any person or entity accessing biological resources or associated traditional knowledge "
                "from India for commercial utilization or bio-survey must obtain prior approval from the "
                "National Biodiversity Authority (NBA) under the Biological Diversity Act 2002."
            ),
            metadata=meta_ayush,
            tags=["biodiversity", "abs", "nba"],
        ),
        KnowledgeDocument(
            doc_id="doc-reg-003",
            title="Ayurvedic Proprietary Medicine Licensing",
            content=(
                "Proprietary Ayurvedic formulations require safety and efficacy documentation as per "
                "Rule 158-B of the Drugs and Cosmetics Rules 1945. Classical formulations listed in "
                "authoritative books of the First Schedule are exempt from clinical trials."
            ),
            metadata=meta_ayush,
            tags=["regulatory", "proprietary", "rule158b"],
        ),
    ]


@pytest.fixture()
def mock_embedding_generator() -> MagicMock:
    gen = MagicMock(spec=EmbeddingGenerator)
    gen.dimension = 128

    def fake_embed_texts(texts): # noqa: ANN001
        n = len(texts)
        if n == 0:
            return np.empty((0, 128), dtype=np.float32)
        vecs = np.random.randn(n, 128).astype(np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / norms

    def fake_embed_query(query): # noqa: ANN001
        vec = np.random.randn(128).astype(np.float32)
        return vec / np.linalg.norm(vec)

    gen.embed_texts.side_effect = fake_embed_texts
    gen.embed_query.side_effect = fake_embed_query
    return gen


@pytest.fixture()
def mock_reranker() -> MagicMock:
    reranker = MagicMock(spec=CrossEncoderReranker)

    def fake_rerank(query, candidates, top_k=5): # noqa: ANN001
        scored = [(cand, float(0.95 - idx * 0.1)) for idx, cand in enumerate(candidates[:top_k])]
        return scored

    reranker.rerank.side_effect = fake_rerank
    return reranker


class TestHybridRAGPipeline:
    def test_end_to_end_build_and_search(
        self,
        synthetic_knowledge_base: list[KnowledgeDocument],
        mock_embedding_generator: MagicMock,
        mock_reranker: MagicMock,
    ) -> None:
        pipeline = HybridRAGPipeline(
            chunker=DocumentChunker(chunk_size=500),
            embedding_generator=mock_embedding_generator,
            faiss_store=FAISSVectorStore(),
            bm25_store=BM25SparseStore(),
            fusion=ReciprocalRankFusion(rrf_k=60),
            reranker=mock_reranker,
        )

        assert not pipeline.is_built

        indexed_count = pipeline.build_index(synthetic_knowledge_base)
        assert indexed_count == 3
        assert pipeline.is_built

        # Search for patent Section 3p query
        query = "What are Section 3p patent rules for traditional knowledge in India?"
        evidence = pipeline.search(query, faiss_top_k=5, bm25_top_k=5, rerank_top_k=2)

        assert len(evidence) == 2
        top_item = evidence[0]

        assert isinstance(top_item, EvidenceChunk)
        assert top_item.rank == 0
        assert top_item.source_label == "[SOURCE_1]"
        assert top_item.content != ""
        assert top_item.source_name in {"IP India Patent Office", "Ministry of AYUSH"}
        assert top_item.authority in {"CGPDTM", "Ministry of AYUSH"}
        assert top_item.publication_date is not None
        assert top_item.jurisdiction == "india"

    def test_save_and_load_index_disk_roundtrip(
        self,
        synthetic_knowledge_base: list[KnowledgeDocument],
        mock_embedding_generator: MagicMock,
        mock_reranker: MagicMock,
        tmp_path: Path,
    ) -> None:
        pipeline = HybridRAGPipeline(
            chunker=DocumentChunker(chunk_size=500),
            embedding_generator=mock_embedding_generator,
            faiss_store=FAISSVectorStore(),
            bm25_store=BM25SparseStore(),
            fusion=ReciprocalRankFusion(rrf_k=60),
            reranker=mock_reranker,
        )

        pipeline.build_index(synthetic_knowledge_base)
        index_dir = tmp_path / "pipeline_indexes"
        pipeline.save_index(index_dir)

        # Create new pipeline and load from disk
        new_pipeline = HybridRAGPipeline(
            embedding_generator=mock_embedding_generator,
            faiss_store=FAISSVectorStore(),
            bm25_store=BM25SparseStore(),
            fusion=ReciprocalRankFusion(rrf_k=60),
            reranker=mock_reranker,
        )
        new_pipeline.load_index(index_dir)

        assert new_pipeline.is_built

        results = new_pipeline.search("Biological Diversity Act NBA approval", rerank_top_k=1)
        assert len(results) == 1
        assert isinstance(results[0], EvidenceChunk)
        assert results[0].source_name in {"IP India Patent Office", "Ministry of AYUSH"}

    def test_empty_query_returns_empty_list(
        self,
        synthetic_knowledge_base: list[KnowledgeDocument],
        mock_embedding_generator: MagicMock,
        mock_reranker: MagicMock,
    ) -> None:
        pipeline = HybridRAGPipeline(
            embedding_generator=mock_embedding_generator,
            reranker=mock_reranker,
        )
        pipeline.build_index(synthetic_knowledge_base)

        assert pipeline.search("   ") == []

    def test_empty_knowledge_base_build(
        self,
        mock_embedding_generator: MagicMock,
        mock_reranker: MagicMock,
    ) -> None:
        pipeline = HybridRAGPipeline(
            embedding_generator=mock_embedding_generator,
            reranker=mock_reranker,
        )
        indexed = pipeline.build_index([])
        assert indexed == 0
        assert not pipeline.is_built

    def test_unbuilt_index_search_returns_empty_list(self) -> None:
        pipeline = HybridRAGPipeline()
        # Search on unbuilt pipeline when index_dir has no files
        assert pipeline.search("patent query") == []
