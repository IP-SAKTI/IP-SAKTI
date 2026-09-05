"""
tests/test_orchestrator/test_classifier.py

Unit tests for ip_sakti.orchestrator.classifier.QueryClassifier.
"""

from __future__ import annotations

import pytest

from ip_sakti.models.query import FormulationCategory, Intent, Jurisdiction
from ip_sakti.orchestrator.classifier import QueryClassifier


@pytest.fixture()
def classifier() -> QueryClassifier:
    return QueryClassifier()


class TestQueryClassifier:
    def test_classify_ip_intent(self, classifier: QueryClassifier) -> None:
        assert classifier.classify_intent("What is the patent filing process in Section 3(p)?") == Intent.IP

    def test_classify_regulatory_intent(self, classifier: QueryClassifier) -> None:
        assert classifier.classify_intent("Ayurvedic drug licensing requirements under Rule 158-B") == Intent.REGULATORY

    def test_classify_ayurvedic_manufacturing_as_regulatory(
        self, classifier: QueryClassifier
    )-> None:
        query = "What are the requirements for manufacturing an Ayurvedic medicine in India?"
        assert classifier.classify_intent(query) == Intent.REGULATORY

    def test_classify_tk_abs_intent(self, classifier: QueryClassifier) -> None:
        assert classifier.classify_intent("National Biodiversity Authority ABS approval for traditional knowledge") == Intent.TK_ABS

    def test_classify_ambiguous_intent(self, classifier: QueryClassifier) -> None:
        assert classifier.classify_intent("Tell me something general") == Intent.AMBIGUOUS

    def test_analyze_jurisdiction_user_override(self, classifier: QueryClassifier) -> None:
        res = classifier.analyze_jurisdiction("wipo pct", user_selected=Jurisdiction.INDIA)
        assert res == Jurisdiction.INDIA

    def test_analyze_jurisdiction_keywords(self, classifier: QueryClassifier) -> None:
        assert classifier.analyze_jurisdiction("patent requirements in India cgdptm") == Jurisdiction.INDIA
        assert classifier.analyze_jurisdiction("wipo pct international filing") == Jurisdiction.INTERNATIONAL
        assert classifier.analyze_jurisdiction("India and wipo international filing") == Jurisdiction.BOTH

    def test_classify_formulation_categories(self, classifier: QueryClassifier) -> None:
        assert classifier.classify_formulation("Ayurvedic cosmetic face cream") == FormulationCategory.COSMETIC
        assert classifier.classify_formulation("Classical Samhita formulation") == FormulationCategory.CLASSICAL
        assert classifier.classify_formulation("Proprietary herbal medicine") == FormulationCategory.PROPRIETARY
        assert classifier.classify_formulation("Ayurveda-Aahar nutraceutical product") == FormulationCategory.NUTRACEUTICAL
