"""
tests/test_e2e_full_flow.py

End-to-end full system request flow tests for IP-SAKTI Sahayak.
Verifies full query processing from entry point through Multilingual,
Orchestrator, Rule Engine, Specialist Agents, Hybrid RAG, Synthesis,
Citation Validation, Confidence Assessment, and SQLite Persistence.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.llm import AnswerSynthesisService, SafeAbstentionHandler
from ip_sakti.models.query import (
    AgentType,
    FinalResponse,
    FormulationCategory,
    Jurisdiction,
    QueryRequest,
)
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.retrieval import HybridRAGPipeline
from ip_sakti.service import IPSAKTIService
from ip_sakti.utils.db import DatabaseManager


@pytest.fixture()
def full_system_service(tmp_path: Path) -> IPSAKTIService:
    db_path = tmp_path / "e2e_full_flow.db"
    db = DatabaseManager(db_path=db_path)
    db.initialise()

    meta_ip = DocumentMetadata(
        source_id="ip_india",
        source_name="CGPDTM Patent Office",
        authority="CGPDTM",
        jurisdiction="india",
    )
    meta_reg = DocumentMetadata(
        source_id="ayush_licensing",
        source_name="Ministry of AYUSH",
        authority="AYUSH",
        jurisdiction="india",
    )
    meta_tk = DocumentMetadata(
        source_id="nba_act",
        source_name="National Biodiversity Authority",
        authority="NBA",
        jurisdiction="india",
    )

    kb_docs = [
        KnowledgeDocument(
            doc_id="doc-ip-1",
            title="Section 3(p) Guidelines",
            content="Section 3(p) excludes traditional knowledge and incremental variations of known plants from patentability.",
            metadata=meta_ip,
        ),
        KnowledgeDocument(
            doc_id="doc-reg-1",
            title="Rule 158-B AYUSH Licensing",
            content="Ayurvedic proprietary medicines require proof of safety and effectiveness under Rule 158-B of Drugs and Cosmetics Rules.",
            metadata=meta_reg,
        ),
        KnowledgeDocument(
            doc_id="doc-tk-1",
            title="Biological Diversity Act Section 3",
            content="Access to biological resources for commercial utilization requires prior approval from National Biodiversity Authority.",
            metadata=meta_tk,
        ),
    ]

    rag = HybridRAGPipeline()
    rag.build_index(kb_docs)

    abstention = SafeAbstentionHandler(db_manager=db)
    synthesis = AnswerSynthesisService(abstention_handler=abstention)
    coordinator = PipelineCoordinator(rag_pipeline=rag, synthesis_service=synthesis)

    return IPSAKTIService(coordinator=coordinator, db_manager=db)


class TestE2EFullFlow:
    def test_e2e_ip_patentability_flow(self, full_system_service: IPSAKTIService) -> None:
        req = QueryRequest(
            raw_query="What are the patentability requirements under Section 3(p) in India?",
            jurisdiction=Jurisdiction.INDIA,
            formulation_category=FormulationCategory.CLASSICAL,
            user_language="en",
        )

        resp = full_system_service.process_query(req)

        assert isinstance(resp, FinalResponse)
        assert resp.query_id == req.query_id
        assert resp.is_abstention is False
        assert AgentType.IP_AGENT in resp.agents_invoked
        assert len(resp.evidence) >= 1
        assert resp.confidence is not None
        assert resp.confidence.score >= 0.5

        # Verify DB entry updated
        conn = full_system_service.db.connection
        row = conn.execute("SELECT agents_invoked, is_abstention FROM queries WHERE query_id = ?", (str(req.query_id),)).fetchone()
        assert row is not None
        assert "ip_agent" in row["agents_invoked"]
        assert row["is_abstention"] == 0

    def test_e2e_regulatory_licensing_flow(self, full_system_service: IPSAKTIService) -> None:
        req = QueryRequest(
            raw_query="What proof is required for AYUSH licensing under Rule 158-B?",
            jurisdiction=Jurisdiction.INDIA,
            formulation_category=FormulationCategory.PROPRIETARY,
            user_language="en",
        )

        resp = full_system_service.process_query(req)

        assert isinstance(resp, FinalResponse)
        assert resp.query_id == req.query_id
        assert resp.is_abstention is False
        assert AgentType.REGULATORY_AGENT in resp.agents_invoked
        assert len(resp.evidence) >= 1

    def test_e2e_tk_abs_biological_resource_flow(self, full_system_service: IPSAKTIService) -> None:
        req = QueryRequest(
            raw_query="Do I need NBA approval for commercial utilization of biological resources under Biological Diversity Act?",
            jurisdiction=Jurisdiction.INDIA,
            user_language="en",
        )

        resp = full_system_service.process_query(req)

        assert isinstance(resp, FinalResponse)
        assert resp.query_id == req.query_id
        assert resp.is_abstention is False
        assert AgentType.TK_ABS_AGENT in resp.agents_invoked
        assert len(resp.evidence) >= 1

    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_e2e_indic_hindi_query_flow(
        self, mock_gt_cls: MagicMock, full_system_service: IPSAKTIService
    ) -> None:
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "What are Section 3(p) patent guidelines?"
        mock_gt_cls.return_value = mock_instance

        req = QueryRequest(
            raw_query="सेक्शन 3(p) पेटेंट नियम क्या हैं?",
            jurisdiction=Jurisdiction.INDIA,
            user_language="hi",
        )

        resp = full_system_service.process_query(req)

        assert isinstance(resp, FinalResponse)
        assert resp.query_id == req.query_id

    def test_e2e_unrelated_query_safe_abstention_and_escalation(self, tmp_path: Path) -> None:
        db_path = tmp_path / "e2e_abstention.db"
        db = DatabaseManager(db_path=db_path)
        db.initialise()

        empty_rag = HybridRAGPipeline()
        abstention = SafeAbstentionHandler(db_manager=db)
        synthesis = AnswerSynthesisService(abstention_handler=abstention)
        coordinator = PipelineCoordinator(rag_pipeline=empty_rag, synthesis_service=synthesis)
        service = IPSAKTIService(coordinator=coordinator, db_manager=db)

        req = QueryRequest(
            raw_query="Completely unrelated medical question with no legal or regulatory data",
            user_language="en",
        )

        resp = service.process_query(req)

        assert isinstance(resp, FinalResponse)
        assert resp.is_abstention is True

        # Verify DB escalation record
        conn = db.connection
        row = conn.execute("SELECT * FROM escalations WHERE query_id = ?", (str(req.query_id),)).fetchone()
        assert row is not None
        assert row["query_id"] == str(req.query_id)
        assert "evidence" in row["reason"].lower() or "insufficient" in row["reason"].lower()
