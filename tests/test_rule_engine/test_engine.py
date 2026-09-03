"""
tests/test_rule_engine/test_engine.py

Unit tests for ip_sakti.rule_engine.engine.RuleEngine.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from ip_sakti.models.query import FormulationCategory, Intent, Jurisdiction, QueryContext
from ip_sakti.rule_engine.engine import RuleEngine


@pytest.fixture()
def rule_engine() -> RuleEngine:
    return RuleEngine()


class TestRuleEngine:
    def test_evaluate_rules_returns_list(self, rule_engine: RuleEngine) -> None:
        ctx = QueryContext(
            query_id=uuid4(),
            raw_query="patent Section 3p rules",
            normalised_query="patent section 3p rules",
            detected_language="en",
            lang_detect_confidence=1.0,
            translated_query="patent section 3p rules",
            intent=Intent.IP,
            jurisdiction=Jurisdiction.INDIA,
            formulation_category=FormulationCategory.CLASSICAL,
        )

        guidance = rule_engine.evaluate_rules(ctx)
        assert isinstance(guidance, list)
