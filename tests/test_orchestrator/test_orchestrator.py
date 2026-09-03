"""
tests/test_orchestrator/test_orchestrator.py

Unit tests for ip_sakti.orchestrator.orchestrator.Orchestrator.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from ip_sakti.models.multilingual import (
    DetectionResult,
    MultilingualContext,
    NormalisationResult,
    TranslationResult,
)
from ip_sakti.models.query import Intent, QueryContext, QueryRequest
from ip_sakti.orchestrator.orchestrator import Orchestrator


@pytest.fixture()
def orchestrator() -> Orchestrator:
    return Orchestrator()


class TestOrchestrator:
    def test_process_builds_query_context(self, orchestrator: Orchestrator) -> None:
        qid = uuid4()
        req = QueryRequest(query_id=qid, raw_query="patent filing section 3p in India")

        m_ctx = MultilingualContext(
            query_id=qid,
            raw_query="patent filing section 3p in India",
            detection=DetectionResult(language="en", confidence=0.99),
            normalisation=NormalisationResult(
                original="patent filing section 3p in India",
                normalised="patent filing section 3p in India",
            ),
            query_translation=TranslationResult(
                source_language="en",
                target_language="en",
                original_text="patent filing section 3p in India",
                translated_text="patent filing section 3p in India",
                was_translated=False,
            ),
            effective_language="en",
        )

        ctx = orchestrator.process(req, m_ctx)

        assert isinstance(ctx, QueryContext)
        assert ctx.query_id == qid
        assert ctx.intent == Intent.IP
        assert ctx.translated_query == "patent filing section 3p in India"
