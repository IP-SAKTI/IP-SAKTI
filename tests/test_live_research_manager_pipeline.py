"""
tests/test_live_research_manager_pipeline.py — Tests for LiveResearchManager, SearchMode routing, and Pipeline Evidence Fusion.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from ip_sakti.models.query import (
    AgentType,
    EvidenceChunk,
    Jurisdiction,
    QueryRequest,
    SearchMode,
)
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.retrieval.live_research_manager import LiveResearchManager
from ip_sakti.retrieval.patent_search import PatentSearchProvider
from ip_sakti.retrieval.web_search import WebSearchProvider


@pytest.fixture
def sample_internal_evidence():
    return [
        EvidenceChunk(
            chunk_id="chunk_internal_1",
            doc_id="doc_internal_1",
            source_id="src_internal_1",
            content="Section 3(p) excludes traditional knowledge from patentability.",
            source_label="[SOURCE_1]",
            source_name="Patents Act 1970",
            rerank_score=0.95,
        ),
    ]


@pytest.fixture
def sample_live_evidence():
    return [
        EvidenceChunk(
            chunk_id="chunk_live_1",
            doc_id="doc_live_1",
            source_id="src_live_1",
            content="AYUSH issued updated 2026 guidelines regarding patent examination.",
            source_label="[SOURCE_1]",
            source_name="Ministry of AYUSH Notice",
            source_url="https://ayush.gov.in/notice-2026.html",
            rerank_score=0.88,
        ),
    ]


def test_should_trigger_live_research():
    manager = LiveResearchManager()

    # SearchMode.INTERNAL always False
    assert manager.should_trigger_live_research("latest guidelines 2026", SearchMode.INTERNAL) is False

    # SearchMode.LIVE always True
    assert manager.should_trigger_live_research("Section 3(p)", SearchMode.LIVE) is True

    # SearchMode.HYBRID triggers on temporal/update keywords
    assert manager.should_trigger_live_research("what are the latest AYUSH guidelines?", SearchMode.HYBRID) is True
    assert manager.should_trigger_live_research("recent changes in 2026", SearchMode.HYBRID) is True
    assert manager.should_trigger_live_research("current patent requirements for ashwagandha", SearchMode.HYBRID) is True

    # SearchMode.HYBRID does not trigger on purely static historical questions
    assert manager.should_trigger_live_research("Explain Section 3(p) of the Patents Act.", SearchMode.HYBRID) is False


def test_evidence_fusion_and_sequential_labeling(sample_internal_evidence, sample_live_evidence):
    manager = LiveResearchManager()

    fused = manager.fuse_evidence(
        internal_evidence=sample_internal_evidence,
        live_evidence=sample_live_evidence,
        search_mode=SearchMode.HYBRID,
    )

    assert len(fused) == 2
    # Check that labels are sequentially re-numbered [SOURCE_1], [SOURCE_2]
    assert fused[0].source_label == "[SOURCE_1]"
    assert fused[1].source_label == "[SOURCE_2]"
    # Rank ordering follows rerank_score
    assert fused[0].rerank_score >= fused[1].rerank_score


def test_live_research_caching(sample_live_evidence):
    mock_web = MagicMock(spec=WebSearchProvider)
    mock_web.search.return_value = sample_live_evidence
    mock_patent = MagicMock(spec=PatentSearchProvider)
    mock_patent.search.return_value = []

    manager = LiveResearchManager(web_provider=mock_web, patent_provider=mock_patent, cache_ttl_seconds=60)

    # First call triggers provider
    res1, _ = manager.conduct_live_research("latest AYUSH notifications", search_mode=SearchMode.LIVE)
    assert len(res1) == 1
    assert mock_web.search.call_count == 1

    # Second call returns from in-memory cache
    res2, _ = manager.conduct_live_research("latest AYUSH notifications", search_mode=SearchMode.LIVE)
    assert len(res2) == 1
    assert mock_web.search.call_count == 1  # Not called again!


def test_pipeline_coordinator_live_research_integration(sample_live_evidence):
    mock_live_mgr = MagicMock(spec=LiveResearchManager)
    mock_live_mgr.conduct_live_research.return_value = (sample_live_evidence, "session-test-uuid")
    mock_live_mgr.fuse_evidence.return_value = sample_live_evidence

    coordinator = PipelineCoordinator(live_research_manager=mock_live_mgr)

    req = QueryRequest(
        raw_query="What are the latest 2026 AYUSH guidelines?",
        jurisdiction=Jurisdiction.INDIA,
        search_mode=SearchMode.HYBRID,
    )

    response = coordinator.execute(req)

    assert response.search_mode == SearchMode.HYBRID
    assert response.live_research_metadata is not None
    assert response.live_research_metadata["research_session_id"] == "session-test-uuid"
    mock_live_mgr.conduct_live_research.assert_called_once()
    mock_live_mgr.fuse_evidence.assert_called_once()


def test_pipeline_live_search_failure_fallback():
    # If live research raises an exception, the coordinator must not crash
    mock_live_mgr = MagicMock(spec=LiveResearchManager)
    mock_live_mgr.conduct_live_research.side_effect = RuntimeError("External web search timed out")
    mock_live_mgr.fuse_evidence.side_effect = lambda internal_evidence, live_evidence, search_mode: internal_evidence

    coordinator = PipelineCoordinator(live_research_manager=mock_live_mgr)

    req = QueryRequest(
        raw_query="What are the recent patent rules?",
        search_mode=SearchMode.LIVE,
    )

    response = coordinator.execute(req)
    # The pipeline should complete without throwing an exception
    assert response is not None
    assert response.live_research_metadata["status"] == "fallback_internal"
