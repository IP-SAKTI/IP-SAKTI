"""
tests/test_pipeline_integration/test_db_logging.py

Database persistence tests for IPSAKTIService.
Verifies that query execution records and escalation records are written to SQLite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.llm import AnswerSynthesisService, SafeAbstentionHandler
from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.models.query import QueryRequest
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.retrieval import HybridRAGPipeline
from ip_sakti.service import IPSAKTIService
from ip_sakti.utils.db import DatabaseManager


@pytest.fixture()
def mock_service(tmp_path: Path) -> IPSAKTIService:
    db_path = tmp_path / "test_db_logging.db"
    db = DatabaseManager(db_path=db_path)
    db.initialise()

    # Build RAG pipeline with 1 doc
    meta = DocumentMetadata(source_id="ip_india", source_name="IP India")
    doc = KnowledgeDocument(
        doc_id="d1", title="Doc 1", content="Patent filing guidelines Section 3p", metadata=meta
    )
    rag = HybridRAGPipeline()
    rag.build_index([doc])

    abstention = SafeAbstentionHandler(db_manager=db)
    synthesis = AnswerSynthesisService(abstention_handler=abstention)
    coord = PipelineCoordinator(rag_pipeline=rag, synthesis_service=synthesis)
    return IPSAKTIService(coordinator=coord, db_manager=db)


class TestServiceDatabaseLogging:
    def test_service_persists_query_to_sqlite(self, mock_service: IPSAKTIService) -> None:
        req = QueryRequest(
            raw_query="What is the patent requirement in Section 3p?",
            user_language="en",
        )
        resp = mock_service.process_query(req)

        assert resp.query_id == req.query_id

        # Verify record in SQLite queries table
        conn = mock_service.db.connection
        cursor = conn.cursor()
        cursor.execute("SELECT query_id, raw_query, is_abstention FROM queries WHERE query_id = ?", (str(req.query_id),))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == str(req.query_id)
        assert row[1] == "What is the patent requirement in Section 3p?"
        assert row[2] in (0, 1)

    def test_service_persists_escalation_to_sqlite(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test_escalations.db"
        db = DatabaseManager(db_path=db_path)
        db.initialise()

        # Unbuilt RAG pipeline forces 0 evidence -> safe abstention
        empty_rag = HybridRAGPipeline()
        abstention = SafeAbstentionHandler(db_manager=db)
        synthesis = AnswerSynthesisService(abstention_handler=abstention)
        coord = PipelineCoordinator(rag_pipeline=empty_rag, synthesis_service=synthesis)
        service = IPSAKTIService(coordinator=coord, db_manager=db)

        req = QueryRequest(
            raw_query="Unrelated topic with zero evidence",
            user_language="en",
        )
        resp = service.process_query(req)

        assert resp.is_abstention is True

        conn = db.connection
        cursor = conn.cursor()
        cursor.execute("SELECT query_id, reason FROM escalations WHERE query_id = ?", (str(req.query_id),))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == str(req.query_id)
        assert "evidence" in row[1].lower() or "insufficient" in row[1].lower()
