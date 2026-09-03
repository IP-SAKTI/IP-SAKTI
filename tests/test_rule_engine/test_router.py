"""
tests/test_rule_engine/test_router.py

Unit tests for ip_sakti.rule_engine.router.AgentRouter.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from ip_sakti.models.query import AgentType, FormulationCategory, Intent, Jurisdiction, QueryContext
from ip_sakti.rule_engine.router import AgentRouter


@pytest.fixture()
def router() -> AgentRouter:
    return AgentRouter()


def _make_context(intent: Intent) -> QueryContext:
    return QueryContext(
        query_id=uuid4(),
        raw_query="test query",
        normalised_query="test query",
        detected_language="en",
        lang_detect_confidence=1.0,
        translated_query="test query",
        intent=intent,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.UNKNOWN,
    )


class TestAgentRouter:
    def test_route_ip_intent(self, router: AgentRouter) -> None:
        routes = router.route(_make_context(Intent.IP))
        assert routes == [AgentType.IP_AGENT]

    def test_route_regulatory_intent(self, router: AgentRouter) -> None:
        routes = router.route(_make_context(Intent.REGULATORY))
        assert routes == [AgentType.REGULATORY_AGENT]

    def test_route_tk_abs_intent(self, router: AgentRouter) -> None:
        routes = router.route(_make_context(Intent.TK_ABS))
        assert routes == [AgentType.TK_ABS_AGENT]

    def test_route_ambiguous_intent(self, router: AgentRouter) -> None:
        routes = router.route(_make_context(Intent.AMBIGUOUS))
        assert len(routes) >= 2
        assert AgentType.IP_AGENT in routes
