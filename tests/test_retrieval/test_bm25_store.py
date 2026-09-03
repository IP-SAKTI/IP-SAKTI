"""
tests/test_retrieval/test_bm25_store.py

Unit tests for ip_sakti.retrieval.bm25_store.BM25SparseStore.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.retrieval.bm25_store import BM25SparseStore
from ip_sakti.retrieval.exceptions import (
    EmptyKnowledgeBaseError,
    IndexNotFoundError,
)


@pytest.fixture()
def sample_chunks() -> list[KnowledgeDocument]:
    meta = DocumentMetadata(source_id="ayush", source_name="Ministry of AYUSH")
    return [
        KnowledgeDocument(
            doc_id="c1",
            title="Ayurveda Patent Guidelines",
            content="Patent filing requirements for Ayurvedic formulation in India Section 3p.",
            metadata=meta,
        ),
        KnowledgeDocument(
            doc_id="c2",
            title="Biodiversity Act and ABS",
            content="Access and Benefit Sharing approval from National Biodiversity Authority.",
            metadata=meta,
        ),
        KnowledgeDocument(
            doc_id="c3",
            title="Cosmetics Rules",
            content="Regulatory provisions for Ayurvedic cosmetic products under Drugs and Cosmetics Act.",
            metadata=meta,
        ),
    ]


class TestBM25SparseStore:
    def test_build_and_search(self, sample_chunks: list[KnowledgeDocument]) -> None:
        store = BM25SparseStore()
        assert not store.is_built

        store.build_index(sample_chunks)
        assert store.is_built
        assert store.num_documents == 3

        results = store.search("patent filing section 3p", top_k=2)
        assert len(results) >= 1
        top_chunk, score = results[0]
        assert top_chunk.doc_id == "c1"
        assert score > 0.0

    def test_save_and_load_roundtrip(
        self, sample_chunks: list[KnowledgeDocument], tmp_path: Path
    ) -> None:
        store = BM25SparseStore()
        store.build_index(sample_chunks)

        save_dir = tmp_path / "bm25_index"
        store.save(save_dir)

        loaded_store = BM25SparseStore()
        loaded_store.load(save_dir)

        assert loaded_store.is_built
        assert loaded_store.num_documents == 3

        results = loaded_store.search("biodiversity access benefit sharing", top_k=1)
        assert len(results) == 1
        assert results[0][0].doc_id == "c2"

    def test_load_missing_files_raises_index_not_found(self, tmp_path: Path) -> None:
        store = BM25SparseStore()
        with pytest.raises(IndexNotFoundError):
            store.load(tmp_path / "non_existent")

    def test_build_empty_chunks_raises_empty_kb_error(self) -> None:
        store = BM25SparseStore()
        with pytest.raises(EmptyKnowledgeBaseError):
            store.build_index([])

    def test_unbuilt_search_returns_empty_list(self) -> None:
        store = BM25SparseStore()
        assert store.search("ayurveda") == []

    def test_empty_query_returns_empty_list(
        self, sample_chunks: list[KnowledgeDocument]
    ) -> None:
        store = BM25SparseStore()
        store.build_index(sample_chunks)
        assert store.search("   ") == []
