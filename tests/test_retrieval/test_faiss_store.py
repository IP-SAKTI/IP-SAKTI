"""
tests/test_retrieval/test_faiss_store.py

Unit tests for ip_sakti.retrieval.faiss_store.FAISSVectorStore.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.retrieval.exceptions import (
    CorruptIndexError,
    EmptyKnowledgeBaseError,
    IndexNotFoundError,
    RetrievalError,
)
from ip_sakti.retrieval.faiss_store import FAISSVectorStore


@pytest.fixture()
def sample_chunks() -> list[KnowledgeDocument]:
    meta = DocumentMetadata(source_id="ip_india", source_name="IP India")
    return [
        KnowledgeDocument(
            doc_id="chunk_1", title="Doc 1", content="Patent filing in India", metadata=meta
        ),
        KnowledgeDocument(
            doc_id="chunk_2", title="Doc 2", content="Ayurvedic formulations Section 3p", metadata=meta
        ),
        KnowledgeDocument(
            doc_id="chunk_3", title="Doc 3", content="Access and Benefit Sharing biological resources", metadata=meta
        ),
    ]


@pytest.fixture()
def sample_embeddings() -> np.ndarray:
    # 3 chunks, 128 dimensions, normalized
    vecs = np.random.randn(3, 128).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


class TestFAISSVectorStore:
    def test_build_and_search(
        self, sample_chunks: list[KnowledgeDocument], sample_embeddings: np.ndarray
    ) -> None:
        store = FAISSVectorStore()
        assert not store.is_built

        store.build_index(sample_chunks, sample_embeddings)
        assert store.is_built
        assert store.num_vectors == 3

        # Search with exact vector of chunk 1
        query_vector = sample_embeddings[0]
        results = store.search(query_vector, top_k=2)

        assert len(results) == 2
        top_chunk, top_score = results[0]
        assert top_chunk.doc_id == "chunk_1"
        assert top_score == pytest.approx(1.0, abs=1e-4)

    def test_save_and_load_roundtrip(
        self,
        sample_chunks: list[KnowledgeDocument],
        sample_embeddings: np.ndarray,
        tmp_path: Path,
    ) -> None:
        store = FAISSVectorStore()
        store.build_index(sample_chunks, sample_embeddings)

        save_dir = tmp_path / "faiss_index"
        store.save(save_dir)

        loaded_store = FAISSVectorStore()
        loaded_store.load(save_dir)

        assert loaded_store.is_built
        assert loaded_store.num_vectors == 3

        results = loaded_store.search(sample_embeddings[1], top_k=1)
        assert len(results) == 1
        assert results[0][0].doc_id == "chunk_2"

    def test_load_missing_dir_raises_index_not_found(self, tmp_path: Path) -> None:
        store = FAISSVectorStore()
        with pytest.raises(IndexNotFoundError):
            store.load(tmp_path / "non_existent")

    def test_build_empty_chunks_raises_empty_kb_error(self) -> None:
        store = FAISSVectorStore()
        with pytest.raises(EmptyKnowledgeBaseError):
            store.build_index([], np.empty((0, 128), dtype=np.float32))

    def test_dimension_mismatch_search_raises_error(
        self, sample_chunks: list[KnowledgeDocument], sample_embeddings: np.ndarray
    ) -> None:
        store = FAISSVectorStore()
        store.build_index(sample_chunks, sample_embeddings)

        wrong_dim_query = np.ones((64,), dtype=np.float32)
        with pytest.raises(RetrievalError, match="dimension"):
            store.search(wrong_dim_query)

    def test_unbuilt_search_returns_empty_list(self) -> None:
        store = FAISSVectorStore()
        assert store.search(np.ones((128,), dtype=np.float32)) == []
