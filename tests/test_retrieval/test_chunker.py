"""
tests/test_retrieval/test_chunker.py

Unit tests for ip_sakti.retrieval.chunker.DocumentChunker.
"""

from __future__ import annotations

from datetime import date

import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.retrieval.chunker import DocumentChunker


@pytest.fixture()
def sample_metadata() -> DocumentMetadata:
    return DocumentMetadata(
        source_id="ip_india",
        source_name="IP India Patent Office",
        source_url="https://www.ipindia.gov.in",
        authority="CGPDTM",
        publication_date=date(2024, 1, 15),
        document_type="guideline",
        jurisdiction="india",
    )


@pytest.fixture()
def short_document(sample_metadata: DocumentMetadata) -> KnowledgeDocument:
    return KnowledgeDocument(
        doc_id="doc-short-1",
        title="Short Patent Guidance",
        content="Patent applications for Ayurvedic formulations must comply with Section 3(p).",
        metadata=sample_metadata,
        tags=["patent", "ayurveda"],
    )


@pytest.fixture()
def long_document(sample_metadata: DocumentMetadata) -> KnowledgeDocument:
    paragraphs = [
        "Section 3(p) of the Indian Patents Act 1970 excludes traditional knowledge from patentability.",
        "An invention which in effect is traditional knowledge or an aggregation or duplication of known properties is not patentable.",
        "However, novel phytopharmaceutical formulations showing surprising synergy beyond additive effects may be patentable.",
        "Applicants must file Form 1 with full specification and list prior-art AYUSH references.",
        "Access and Benefit Sharing approval from the National Biodiversity Authority is mandatory if biological resources are used.",
    ]
    return KnowledgeDocument(
        doc_id="doc-long-1",
        title="Comprehensive Ayurvedic Patent & Regulatory Guidelines",
        content=" ".join(paragraphs),
        metadata=sample_metadata,
        tags=["patent", "tk", "abs"],
    )


class TestDocumentChunker:
    def test_short_document_returns_single_chunk(self, short_document: KnowledgeDocument) -> None:
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.chunk_document(short_document)

        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk.parent_doc_id == "doc-short-1"
        assert chunk.doc_id == "doc-short-1_chunk_0"
        assert chunk.chunk_index == 0
        assert chunk.title == "Short Patent Guidance"
        assert chunk.metadata.source_id == "ip_india"
        assert chunk.metadata.source_name == "IP India Patent Office"
        assert chunk.metadata.authority == "CGPDTM"
        assert chunk.metadata.publication_date == date(2024, 1, 15)

    def test_long_document_returns_multiple_chunks(self, long_document: KnowledgeDocument) -> None:
        chunker = DocumentChunker(chunk_size=150, chunk_overlap=30)
        chunks = chunker.chunk_document(long_document)

        assert len(chunks) > 1
        for idx, chunk in enumerate(chunks):
            assert chunk.parent_doc_id == "doc-long-1"
            assert chunk.chunk_index == idx
            assert chunk.metadata.source_name == "IP India Patent Office"
            assert "abs" in chunk.tags

    def test_chunk_documents_multiple(
        self, short_document: KnowledgeDocument, long_document: KnowledgeDocument
    ) -> None:
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
        all_chunks = chunker.chunk_documents([short_document, long_document])

        assert len(all_chunks) >= 2
        parent_ids = {c.parent_doc_id for c in all_chunks}
        assert "doc-short-1" in parent_ids
        assert "doc-long-1" in parent_ids

    def test_empty_document_content_returns_empty_list(
        self, sample_metadata: DocumentMetadata
    ) -> None:
        doc = KnowledgeDocument(
            doc_id="empty-1",
            title="Empty Doc",
            content="   ",
            metadata=sample_metadata,
        )
        chunker = DocumentChunker()
        assert chunker.chunk_document(doc) == []

    def test_invalid_parameters_raise_value_error(self) -> None:
        with pytest.raises(ValueError):
            DocumentChunker(chunk_size=0)

        with pytest.raises(ValueError):
            DocumentChunker(chunk_size=100, chunk_overlap=100)

        with pytest.raises(ValueError):
            DocumentChunker(chunk_size=100, chunk_overlap=-10)
