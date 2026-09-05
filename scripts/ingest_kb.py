"""
scripts/ingest_kb.py — Knowledge Base Ingestion & Dual RAG Index Builder.

Ingests authoritative legal and regulatory documents from data/knowledge/,
validates provenance against SourceRegistry, chunks text, generates embeddings,
builds FAISS & BM25 indexes, saves indexes to disk (indexes/), and populates the
SQLite documents table.

Usage:
    python scripts/ingest_kb.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.retrieval import (
    BM25SparseStore,
    DocumentChunker,
    EmbeddingGenerator,
    FAISSVectorStore,
    HybridRAGPipeline,
    SourceRegistry,
)
from ip_sakti.utils.config import get_settings
from ip_sakti.utils.db import DatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_ingestion(
    data_dir: Path | str | None = None,
    index_dir: Path | str | None = None,
    db_path: Path | str | None = None,
) -> dict:
    """
    Run full knowledge base ingestion pipeline.

    Returns dict containing diagnostic summary metrics.
    """
    cfg = get_settings()
    root_data = Path(data_dir or cfg.get("paths", {}).get("data_dir", "data/"))
    knowledge_dir = root_data / "knowledge"
    target_index_dir = Path(index_dir or cfg.get("paths", {}).get("index_dir", "indexes/"))

    db_mgr = DatabaseManager(db_path=str(db_path) if db_path else None)
    db_mgr.initialise()

    registry = SourceRegistry()
    registered_sources = registry.list_sources()

    logger.info("Starting Knowledge Base Ingestion...")
    logger.info(f"Registered Authorised Sources: {len(registered_sources)}")

    if not knowledge_dir.exists():
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        logger.warning(f"Created empty directory at {knowledge_dir}")

    doc_files = list(knowledge_dir.glob("*.json"))
    logger.info(f"Found {len(doc_files)} raw document files in {knowledge_dir}")

    documents: list[KnowledgeDocument] = []
    failed_sources: list[str] = []

    for file_path in doc_files:
        try:
            with file_path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            doc = KnowledgeDocument.model_validate(raw)

            # Validate source_id against registry
            source_meta = registry.get_source(doc.metadata.source_id)
            if source_meta:
                # Fill missing metadata from central registry if needed
                if not doc.metadata.source_url:
                    doc.metadata.source_url = source_meta.url
                if not doc.metadata.authority:
                    doc.metadata.authority = source_meta.organisation

            documents.append(doc)
            logger.info(f"Loaded document: '{doc.title}' (ID: {doc.doc_id})")
        except Exception as exc:
            logger.error(f"Failed to process document file {file_path}: {exc}")
            failed_sources.append(file_path.name)

    if not documents:
        logger.error("No valid documents loaded. Ingestion aborted.")
        return {
            "sources_configured": len(registered_sources),
            "documents": 0,
            "chunks": 0,
            "faiss_vectors": 0,
            "bm25_documents": 0,
        }

    # Initialize RAG Pipeline components
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    embedder = EmbeddingGenerator()
    faiss_store = FAISSVectorStore()
    bm25_store = BM25SparseStore()
    pipeline = HybridRAGPipeline(
        chunker=chunker,
        embedding_generator=embedder,
        faiss_store=faiss_store,
        bm25_store=bm25_store,
    )

    # Build and Save Indexes
    total_chunks = pipeline.build_index(documents)
    pipeline.save_index(target_index_dir)

    # Populate SQLite documents table
    chunks = pipeline.chunker.chunk_documents(documents)
    conn = db_mgr.connection
    with conn:
        # Clear existing documents
        conn.execute("DELETE FROM documents")
        for chunk in chunks:
            meta = chunk.metadata
            tags_json = json.dumps(chunk.tags) if chunk.tags else "[]"
            conn.execute(
                """
                INSERT INTO documents (
                    doc_id, title, source_id, source_name, source_url,
                    authority, document_type, jurisdiction, language,
                    publication_date, permitted_use, tags, chunk_index,
                    parent_doc_id, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now'))
                """,
                (
                    chunk.doc_id,
                    chunk.title,
                    meta.source_id,
                    meta.source_name,
                    meta.source_url,
                    meta.authority,
                    meta.document_type,
                    meta.jurisdiction,
                    meta.language,
                    str(meta.publication_date) if meta.publication_date else None,
                    1 if meta.permitted_use else 0,
                    tags_json,
                    chunk.chunk_index,
                    chunk.parent_doc_id,
                ),
            )

    chunks_with_url = sum(1 for c in chunks if c.metadata.source_url)

    stats = {
        "sources_configured": len(registered_sources),
        "successfully_fetched": len(documents),
        "failed_sources": len(failed_sources),
        "documents": len(documents),
        "chunks": total_chunks,
        "faiss_vectors": pipeline.faiss_store.num_vectors,
        "bm25_documents": pipeline.bm25_store.num_documents,
        "chunks_with_valid_citations": chunks_with_url,
    }

    print("\n" + "=" * 50)
    print("INGESTION & INDEXING SUMMARY (Phase 5)")
    print("=" * 50)
    print(f"Authorised sources configured: {stats['sources_configured']}")
    print(f"Successfully loaded:           {stats['successfully_fetched']}")
    print(f"Failed sources:                {stats['failed_sources']}")
    print(f"Documents created:             {stats['documents']}")
    print(f"Chunks generated:              {stats['chunks']}")
    print(f"FAISS vectors:                 {stats['faiss_vectors']}")
    print(f"BM25 documents:                {stats['bm25_documents']}")
    print(f"Chunks with valid citations:   {stats['chunks_with_valid_citations']}")
    print("=" * 50 + "\n")

    return stats


if __name__ == "__main__":
    run_ingestion()
