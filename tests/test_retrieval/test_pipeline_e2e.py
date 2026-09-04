"""
tests/test_retrieval/test_pipeline_e2e.py

Real end-to-end integration test for ip_sakti.retrieval.pipeline.HybridRAGPipeline.

Unlike test_pipeline.py (which mocks embeddings and the cross-encoder), this
module loads the *actual* pretrained SentenceTransformer and CrossEncoder models
and drives the complete pipeline:

    KnowledgeDocuments
        -> DocumentChunker
        -> EmbeddingGenerator (sentence-transformers, real model)
        -> FAISSVectorStore.build_index
        -> BM25SparseStore.build_index
        -> HybridRAGPipeline.search
              -> FAISS dense search
              -> BM25 sparse search
              -> ReciprocalRankFusion
              -> CrossEncoderReranker (real model)
        -> list[EvidenceChunk]  (provenance preserved)

Marked with ``@pytest.mark.integration`` so they can be excluded from fast
unit-test runs:  ``pytest -m "not integration"``
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

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

pytestmark = pytest.mark.integration

_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_CROSS_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def embedding_generator() -> EmbeddingGenerator:
    """Real EmbeddingGenerator backed by the multilingual MiniLM model."""
    return EmbeddingGenerator(model_name=_EMBED_MODEL)


@pytest.fixture(scope="module")
def cross_encoder_reranker() -> CrossEncoderReranker:
    """Real CrossEncoderReranker backed by MiniLM cross-encoder."""
    return CrossEncoderReranker(model_name=_CROSS_MODEL)


@pytest.fixture(scope="module")
def sample_documents() -> list[KnowledgeDocument]:
    """Curated Ayurveda / IP knowledge documents spanning IP, Regulatory, TK/ABS domains."""
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
    meta_wipo = DocumentMetadata(
        source_id="wipo",
        source_name="WIPO",
        source_url="https://www.wipo.int/tk/en",
        authority="World Intellectual Property Organization",
        publication_date=date(2022, 11, 1),
        document_type="treaty",
        jurisdiction="international",
    )

    return [
        KnowledgeDocument(
            doc_id="doc-e2e-001",
            title="Section 3(p) Patent Exclusion for Traditional Knowledge",
            content=(
                "Section 3(p) of the Indian Patents Act 1970 excludes inventions which are "
                "in effect traditional knowledge or an aggregation or duplication of known "
                "properties of traditionally known components from patentability. "
                "The purpose of this provision is to safeguard India's rich heritage of "
                "traditional knowledge from biopiracy and prevent unjust monopolies over "
                "publicly available Ayurvedic knowledge already documented in classical texts."
            ),
            metadata=meta_ip,
            tags=["patent", "traditional_knowledge", "section3p", "india"],
        ),
        KnowledgeDocument(
            doc_id="doc-e2e-002",
            title="National Biodiversity Authority ABS Compliance Requirements",
            content=(
                "Any person or entity accessing biological resources or associated traditional "
                "knowledge from India for commercial utilization or bio-survey and bio-utilization "
                "must obtain prior approval from the National Biodiversity Authority (NBA) under "
                "Section 3 of the Biological Diversity Act 2002. "
                "Access and benefit sharing (ABS) agreements must be signed before any use of "
                "biological materials for research, commercial application, or intellectual property "
                "filings. Violation attracts penalties under Section 55 of the Act."
            ),
            metadata=meta_ayush,
            tags=["biodiversity", "abs", "nba", "biological_diversity_act"],
        ),
        KnowledgeDocument(
            doc_id="doc-e2e-003",
            title="Ayurvedic Proprietary Medicine Licensing under Drugs and Cosmetics Rules",
            content=(
                "Proprietary Ayurvedic formulations require safety and efficacy documentation as "
                "per Rule 158-B of the Drugs and Cosmetics Rules 1945. "
                "Classical Ayurvedic formulations listed in authoritative Ayurvedic books included "
                "in the First Schedule of the Drugs and Cosmetics Act are exempt from clinical "
                "trials but must still obtain a manufacturing licence from the State Licensing "
                "Authority under Form 25-D."
            ),
            metadata=meta_ayush,
            tags=["regulatory", "proprietary", "rule158b", "licensing"],
        ),
        KnowledgeDocument(
            doc_id="doc-e2e-004",
            title="WIPO Intergovernmental Committee on TK and Genetic Resources",
            content=(
                "The WIPO Intergovernmental Committee on Intellectual Property and Genetic "
                "Resources, Traditional Knowledge and Folklore (IGC) negotiates international "
                "instruments for the protection of traditional knowledge, genetic resources, and "
                "traditional cultural expressions. "
                "The IGC's work is intended to establish legally binding norms preventing "
                "misappropriation of indigenous and local community knowledge in patent filings "
                "worldwide. Members may oppose patents granted in error using WIPO opposition "
                "procedures and national patent office re-examination channels."
            ),
            metadata=meta_wipo,
            tags=["wipo", "igc", "traditional_knowledge", "international"],
        ),
        KnowledgeDocument(
            doc_id="doc-e2e-005",
            title="Ayurveda Trademark Protection for Product Brands",
            content=(
                "Ayurvedic product manufacturers can protect their brand names and logos as "
                "trademarks under the Trade Marks Act 1999. Registration with the Trade Marks "
                "Registry at IP India provides exclusive rights to use the mark in connection with "
                "Ayurvedic goods. Common law passing-off action is also available for unregistered "
                "marks. Geographical Indications under the Geographical Indications of Goods Act "
                "1999 may also be obtained for regional Ayurvedic preparations."
            ),
            metadata=meta_ip,
            tags=["trademark", "gi", "brand", "ayurveda", "india"],
        ),
    ]


@pytest.fixture(scope="module")
def built_pipeline(
    embedding_generator: EmbeddingGenerator,
    cross_encoder_reranker: CrossEncoderReranker,
    sample_documents: list[KnowledgeDocument],
) -> HybridRAGPipeline:
    """Fully-indexed HybridRAGPipeline using real models. Built once per module."""
    pipeline = HybridRAGPipeline(
        chunker=DocumentChunker(chunk_size=400, chunk_overlap=50),
        embedding_generator=embedding_generator,
        faiss_store=FAISSVectorStore(),
        bm25_store=BM25SparseStore(),
        fusion=ReciprocalRankFusion(rrf_k=60),
        reranker=cross_encoder_reranker,
    )
    count = pipeline.build_index(sample_documents)
    assert count >= len(sample_documents), (
        f"Expected at least {len(sample_documents)} chunks, got {count}"
    )
    return pipeline


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHybridRAGPipelineE2E:
    """End-to-end integration tests using real pretrained models."""

    # ── Pipeline build ────────────────────────────────────────────────────────

    def test_pipeline_is_built_after_index(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """Both FAISS and BM25 indexes must report is_built == True."""
        assert built_pipeline.is_built
        assert built_pipeline.faiss_store.is_built
        assert built_pipeline.bm25_store.is_built

    def test_index_chunk_count_matches_documents(
        self,
        embedding_generator: EmbeddingGenerator,
        cross_encoder_reranker: CrossEncoderReranker,
        sample_documents: list[KnowledgeDocument],
    ) -> None:
        """Documents with content <= chunk_size must produce exactly one chunk each."""
        pipeline = HybridRAGPipeline(
            chunker=DocumentChunker(chunk_size=2000, chunk_overlap=0),
            embedding_generator=embedding_generator,
            faiss_store=FAISSVectorStore(),
            bm25_store=BM25SparseStore(),
            fusion=ReciprocalRankFusion(rrf_k=60),
            reranker=cross_encoder_reranker,
        )
        count = pipeline.build_index(sample_documents)
        assert count == len(sample_documents)

    # ── Search result structure ───────────────────────────────────────────────

    def test_search_returns_evidence_chunk_list(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """search() must return a non-empty list of EvidenceChunk instances."""
        results = built_pipeline.search(
            "patent exclusion for traditional Ayurvedic knowledge India",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=3,
        )
        assert isinstance(results, list)
        assert len(results) > 0
        for item in results:
            assert isinstance(item, EvidenceChunk)

    def test_search_result_count_respects_rerank_top_k(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """Result count must not exceed rerank_top_k."""
        for top_k in (1, 2, 3):
            results = built_pipeline.search(
                "Ayurvedic drug licensing regulation India",
                faiss_top_k=10,
                bm25_top_k=10,
                rerank_top_k=top_k,
            )
            assert len(results) <= top_k, (
                f"Expected <= {top_k} results, got {len(results)}"
            )

    # ── Ranking and scores ────────────────────────────────────────────────────

    def test_evidence_chunks_are_rank_ordered(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """rank field must increment from 0; rerank_score must be non-increasing."""
        results = built_pipeline.search(
            "biological diversity act NBA access benefit sharing",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=3,
        )
        assert len(results) > 0
        for expected_rank, chunk in enumerate(results):
            assert chunk.rank == expected_rank, (
                f"Expected rank={expected_rank}, got {chunk.rank}"
            )
        rerank_scores = [c.rerank_score for c in results if c.rerank_score is not None]
        if len(rerank_scores) > 1:
            for i in range(len(rerank_scores) - 1):
                assert rerank_scores[i] >= rerank_scores[i + 1], (
                    f"rerank_scores not monotonically non-increasing at index {i}: "
                    f"{rerank_scores[i]:.4f} < {rerank_scores[i + 1]:.4f}"
                )

    def test_rrf_scores_are_positive(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """All evidence chunks must carry a positive rrf_score."""
        results = built_pipeline.search(
            "traditional knowledge patent exclusion section 3p",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=5,
        )
        for chunk in results:
            assert chunk.rrf_score is not None
            assert chunk.rrf_score > 0.0, (
                f"chunk {chunk.chunk_id} has non-positive rrf_score={chunk.rrf_score}"
            )

    # ── Provenance preservation ───────────────────────────────────────────────

    def test_evidence_chunk_provenance_fields_populated(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """Every returned EvidenceChunk must have all required provenance fields."""
        results = built_pipeline.search(
            "Ayurvedic trademark brand protection IP India",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=3,
        )
        assert len(results) > 0
        for chunk in results:
            assert chunk.chunk_id, "chunk_id must be non-empty"
            assert chunk.doc_id, "doc_id must be non-empty"
            assert chunk.content, "content must be non-empty"
            assert chunk.source_label.startswith("[SOURCE_"), (
                f"Unexpected source_label: {chunk.source_label!r}"
            )
            assert chunk.source_name, "source_name must be non-empty"
            assert chunk.authority is not None, "authority must be set"
            assert chunk.jurisdiction is not None, "jurisdiction must be set"
            assert chunk.publication_date is not None, "publication_date must be set"
            assert chunk.document_type is not None, "document_type must be set"
            assert chunk.source_url is not None, "source_url must be set"

    def test_source_labels_are_sequential(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """source_label must be [SOURCE_1], [SOURCE_2], ... in result order."""
        results = built_pipeline.search(
            "WIPO intergovernmental committee traditional knowledge IGC",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=4,
        )
        for i, chunk in enumerate(results):
            expected_label = f"[SOURCE_{i + 1}]"
            assert chunk.source_label == expected_label, (
                f"Expected {expected_label!r}, got {chunk.source_label!r}"
            )

    def test_content_is_non_empty_string(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """Every evidence chunk must have non-empty content text."""
        results = built_pipeline.search(
            "Ayurvedic proprietary medicine rule 158B clinical trials",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=3,
        )
        for chunk in results:
            assert isinstance(chunk.content, str)
            assert len(chunk.content.strip()) > 0

    # ── Semantic relevance ────────────────────────────────────────────────────

    def test_top_result_semantically_relevant_patent_query(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """For a clear patent/TK query, at least one top result must contain patent-related content."""
        results = built_pipeline.search(
            "Can I patent an Ayurvedic formulation based on traditional knowledge?",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=3,
        )
        assert len(results) > 0
        patent_keywords = {
            "patent", "traditional", "knowledge", "section",
            "biodiversity", "patentability", "trademark", "wipo", "ayurvedic",
        }
        found = any(
            patent_keywords & set(c.content.lower().split())
            for c in results
        )
        assert found, (
            f"None of the top results appear semantically relevant to a patent/TK query.\n"
            f"Contents: {[c.content[:120] for c in results]}"
        )

    def test_top_result_semantically_relevant_abs_query(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """For an ABS-specific query, a high-ranking result must mention NBA or Biological Diversity."""
        results = built_pipeline.search(
            "access and benefit sharing biological resources NBA approval",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=3,
        )
        assert len(results) > 0
        abs_keywords = {"nba", "biological", "diversity", "access", "benefit", "sharing"}
        found = any(
            abs_keywords & set(c.content.lower().split())
            for c in results
        )
        assert found, (
            "No result among top-3 mentions ABS / NBA / Biological Diversity. "
            f"Contents: {[c.content[:100] for c in results]}"
        )

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_empty_query_returns_empty_list(
        self, built_pipeline: HybridRAGPipeline
    ) -> None:
        """Empty or whitespace-only queries must return [] without raising."""
        assert built_pipeline.search("") == []
        assert built_pipeline.search("   ") == []

    def test_unbuilt_pipeline_search_returns_empty(self) -> None:
        """A pipeline with no index must return [] rather than raise."""
        pipeline = HybridRAGPipeline()
        result = pipeline.search("patent traditional knowledge India")
        assert result == []

    def test_single_document_pipeline(
        self,
        embedding_generator: EmbeddingGenerator,
        cross_encoder_reranker: CrossEncoderReranker,
        sample_documents: list[KnowledgeDocument],
    ) -> None:
        """Pipeline must work correctly with exactly one document in the knowledge base."""
        pipeline = HybridRAGPipeline(
            chunker=DocumentChunker(chunk_size=2000, chunk_overlap=0),
            embedding_generator=embedding_generator,
            faiss_store=FAISSVectorStore(),
            bm25_store=BM25SparseStore(),
            fusion=ReciprocalRankFusion(rrf_k=60),
            reranker=cross_encoder_reranker,
        )
        pipeline.build_index([sample_documents[0]])
        results = pipeline.search(
            "traditional knowledge patent India",
            faiss_top_k=3,
            bm25_top_k=3,
            rerank_top_k=1,
        )
        assert len(results) == 1
        assert isinstance(results[0], EvidenceChunk)

    # ── Disk persistence round-trip ───────────────────────────────────────────

    def test_save_and_load_preserves_search_results(
        self,
        embedding_generator: EmbeddingGenerator,
        cross_encoder_reranker: CrossEncoderReranker,
        sample_documents: list[KnowledgeDocument],
        tmp_path: Path,
    ) -> None:
        """
        Save FAISS + BM25 indexes to disk, reload into a fresh pipeline,
        and confirm search returns EvidenceChunks with correct provenance.
        """
        index_dir = tmp_path / "e2e_indexes"

        pipeline_a = HybridRAGPipeline(
            chunker=DocumentChunker(chunk_size=400, chunk_overlap=50),
            embedding_generator=embedding_generator,
            faiss_store=FAISSVectorStore(),
            bm25_store=BM25SparseStore(),
            fusion=ReciprocalRankFusion(rrf_k=60),
            reranker=cross_encoder_reranker,
        )
        pipeline_a.build_index(sample_documents)
        pipeline_a.save_index(index_dir)

        pipeline_b = HybridRAGPipeline(
            embedding_generator=embedding_generator,
            faiss_store=FAISSVectorStore(),
            bm25_store=BM25SparseStore(),
            fusion=ReciprocalRankFusion(rrf_k=60),
            reranker=cross_encoder_reranker,
        )
        pipeline_b.load_index(index_dir)
        assert pipeline_b.is_built

        results = pipeline_b.search(
            "NBA biodiversity access benefit sharing India",
            faiss_top_k=5,
            bm25_top_k=5,
            rerank_top_k=2,
        )
        assert len(results) > 0
        top = results[0]
        assert top.source_name
        assert top.authority
        assert top.jurisdiction
        assert top.publication_date is not None
        assert top.source_url

    # ── Embedding vector sanity ───────────────────────────────────────────────

    def test_embedding_vectors_are_normalized(
        self, embedding_generator: EmbeddingGenerator
    ) -> None:
        """Embeddings from the real model must have L2 norm ~= 1.0."""
        texts = [
            "patent exclusion traditional knowledge",
            "ABS compliance National Biodiversity Authority",
        ]
        vecs = embedding_generator.embed_texts(texts)
        assert vecs.shape == (2, embedding_generator.dimension)
        assert vecs.dtype == np.float32
        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-4)

    def test_embed_query_produces_1d_vector(
        self, embedding_generator: EmbeddingGenerator
    ) -> None:
        """embed_query must return a 1-D float32 array of the model's dimension."""
        vec = embedding_generator.embed_query("Ayurvedic formulation licensing")
        assert vec.ndim == 1
        assert vec.shape == (embedding_generator.dimension,)
        assert vec.dtype == np.float32

    def test_embed_empty_texts_shape_when_unloaded(self) -> None:
        """
        embed_texts([]) on a fresh generator (model not yet loaded) must return
        shape (0, 0) — not (0, 384). Validates the robustness fix in embeddings.py.
        """
        gen = EmbeddingGenerator(model_name=_EMBED_MODEL)
        gen._model = None  # noqa: SLF001  (test-only: force unloaded state)
        empty = gen.embed_texts([])
        assert empty.shape == (0, 0), (
            f"Expected (0, 0) for unloaded model, got {empty.shape}"
        )
        assert empty.dtype == np.float32

    def test_embed_empty_texts_correct_dim_when_loaded(
        self, embedding_generator: EmbeddingGenerator
    ) -> None:
        """
        embed_texts([]) when the model is already loaded must return shape
        (0, model.dimension) — not (0, 0) or (0, 384).
        """
        _ = embedding_generator.embed_query("warmup call to ensure model is loaded")
        empty = embedding_generator.embed_texts([])
        assert empty.shape == (0, embedding_generator.dimension), (
            f"Expected (0, {embedding_generator.dimension}), got {empty.shape}"
        )
        assert empty.dtype == np.float32

