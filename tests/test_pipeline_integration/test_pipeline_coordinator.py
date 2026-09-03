"""
tests/test_pipeline_integration/test_pipeline_coordinator.py

Integration tests for ip_sakti.pipeline.PipelineCoordinator.
Uses mock components to test end-to-end execution without external API or model weight dependencies.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from ip_sakti.models.document import DocumentMetadata, KnowledgeDocument
from ip_sakti.models.query import FinalResponse, FormulationCategory, Intent, Jurisdiction, QueryRequest
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.retrieval import HybridRAGPipeline


@pytest.fixture()
def synthetic_kb() -> list[KnowledgeDocument]:
    meta = DocumentMetadata(
        source_id="ip_india",
        source_name="IP India Patent Office",
        authority="CGPDTM",
        jurisdiction="india",
    )
    return [
        KnowledgeDocument(
            doc_id="doc-pat-1",
            title="Section 3(p) Patent Rules",
            content="Section 3(p) excludes traditional knowledge from patentability in India.",
            metadata=meta,
        ),
        KnowledgeDocument(
            doc_id="doc-pat-2",
            title="Form 1 Patent Filing Procedure",
            content="Applicants filing patent applications must submit Form 1 with full technical specification.",
            metadata=meta,
        ),
    ]


@pytest.fixture()
def mock_rag_pipeline(synthetic_kb: list[KnowledgeDocument]) -> HybridRAGPipeline:
    pipeline = HybridRAGPipeline()
    pipeline.build_index(synthetic_kb)
    return pipeline


class TestPipelineCoordinatorIntegration:
    def test_full_pipeline_english_ip_query(self, mock_rag_pipeline: HybridRAGPipeline) -> None:
        coordinator = PipelineCoordinator(rag_pipeline=mock_rag_pipeline)
        req = QueryRequest(
            raw_query="What is the patent filing rule under Section 3(p) in India?",
            user_language="en",
        )

        response = coordinator.execute(req)

        assert isinstance(response, FinalResponse)
        assert response.query_id == req.query_id
        assert response.is_abstention is False
        assert len(response.evidence) >= 1
        assert response.disclaimer != ""

    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_full_pipeline_hindi_regulatory_query(
        self, mock_gt_cls: MagicMock, mock_rag_pipeline: HybridRAGPipeline
    ) -> None:
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "Ayurvedic drug licensing requirements under Rule 158-B"
        mock_gt_cls.return_value = mock_instance

        coordinator = PipelineCoordinator(rag_pipeline=mock_rag_pipeline)
        req = QueryRequest(
            raw_query="आयुर्वेदिक दवा लाइसेंस के नियम क्या हैं?",
            user_language="hi",
        )

        response = coordinator.execute(req)

        assert isinstance(response, FinalResponse)
        assert response.query_id == req.query_id

    def test_full_pipeline_safe_abstention_trigger(self) -> None:
        empty_pipeline = HybridRAGPipeline()
        coordinator = PipelineCoordinator(rag_pipeline=empty_pipeline)

        req = QueryRequest(
            raw_query="Unrelated rare topic with no evidence in KB",
            user_language="en",
        )

        response = coordinator.execute(req)

        assert isinstance(response, FinalResponse)
        assert response.is_abstention is True
        assert "insufficient" in response.answer.lower() or "cannot provide" in response.answer.lower()
