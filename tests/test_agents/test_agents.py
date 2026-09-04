"""
tests/test_agents/test_agents.py

Unit tests for IPAgent, RegulatoryAgent, and TKABSAgent.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ip_sakti.agents import IPAgent, RegulatoryAgent, TKABSAgent
from ip_sakti.models.document import DocumentMetadata
from ip_sakti.models.query import AgentResult, AgentType, EvidenceChunk, FormulationCategory, Intent, Jurisdiction, QueryContext
from ip_sakti.retrieval.pipeline import HybridRAGPipeline


@pytest.fixture()
def mock_pipeline() -> MagicMock:
    pipeline = MagicMock(spec=HybridRAGPipeline)
    chunk = EvidenceChunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        content="Patent filing requirements under Section 3(p).",
        source_label="[SOURCE_1]",
        source_name="IP India",
    )
    pipeline.search.return_value = [chunk]
    return pipeline


@pytest.fixture()
def sample_context() -> QueryContext:
    return QueryContext(
        query_id=uuid4(),
        raw_query="patent application",
        normalised_query="patent application",
        detected_language="en",
        lang_detect_confidence=1.0,
        translated_query="patent application",
        intent=Intent.IP,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.CLASSICAL,
    )


class TestAgents:
    def test_ip_agent_process(self, sample_context: QueryContext, mock_pipeline: MagicMock) -> None:
        agent = IPAgent()
        assert agent.agent_type == AgentType.IP_AGENT

        res = agent.process(sample_context, mock_pipeline)
        assert isinstance(res, AgentResult)
        assert res.agent_type == AgentType.IP_AGENT
        assert len(res.evidence) == 1

    def test_regulatory_agent_process(self, sample_context: QueryContext, mock_pipeline: MagicMock) -> None:
        agent = RegulatoryAgent()
        assert agent.agent_type == AgentType.REGULATORY_AGENT

        res = agent.process(sample_context, mock_pipeline)
        assert isinstance(res, AgentResult)
        assert res.agent_type == AgentType.REGULATORY_AGENT

    def test_tk_abs_agent_process(self, sample_context: QueryContext, mock_pipeline: MagicMock) -> None:
        agent = TKABSAgent()
        assert agent.agent_type == AgentType.TK_ABS_AGENT

        res = agent.process(sample_context, mock_pipeline)
        assert isinstance(res, AgentResult)
        assert res.agent_type == AgentType.TK_ABS_AGENT

    def test_agent_query_enrichment(self, mock_pipeline: MagicMock) -> None:
        generic_context = QueryContext(
            query_id=uuid4(),
            raw_query="neem formulation",
            normalised_query="neem formulation",
            detected_language="en",
            lang_detect_confidence=1.0,
            translated_query="neem formulation",
            intent=Intent.AMBIGUOUS,
            jurisdiction=Jurisdiction.INDIA,
            formulation_category=FormulationCategory.CLASSICAL,
        )

        # IPAgent enriches generic query
        ip_agent = IPAgent()
        ip_agent.process(generic_context, mock_pipeline)
        called_query = mock_pipeline.search.call_args[0][0]
        assert "patentability" in called_query

        # RegulatoryAgent enriches generic query
        reg_agent = RegulatoryAgent()
        reg_agent.process(generic_context, mock_pipeline)
        called_query = mock_pipeline.search.call_args[0][0]
        assert "Rule 158B" in called_query

        # TKABSAgent enriches generic query
        tk_agent = TKABSAgent()
        tk_agent.process(generic_context, mock_pipeline)
        called_query = mock_pipeline.search.call_args[0][0]
        assert "Traditional Knowledge" in called_query
