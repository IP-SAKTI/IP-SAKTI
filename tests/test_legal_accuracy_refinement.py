"""
tests.test_legal_accuracy_refinement — Authoritative legal accuracy refinement test suite.

Verifies the 5 required prompt test cases:
1. Proprietary Ayurvedic manufacturing licence & Form 24D distinction.
2. New Ayurvedic formulation patentability & TKDL search tool role.
3. Multilingual Hindi commercial Ayurvedic manufacturing & patent query.
4. Multilingual Malayalam TKDL & prior art patentability query.
5. Safe abstention multi-jurisdictional Antarctica fee query.
"""

import os
import pytest

from ip_sakti.models.query import QueryRequest
from ip_sakti.pipeline import PipelineCoordinator


@pytest.fixture
def coordinator():
    """Initialise PipelineCoordinator with offline settings."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    return PipelineCoordinator()


def test_proprietary_ayurvedic_manufacturing_licence(coordinator):
    """TEST 1: Proprietary Ayurvedic manufacturing licence, Form 24D, technical personnel, Schedule T GMP."""
    query = (
        "An Ayurvedic company wants to manufacture a proprietary medicine for commercial sale in India. "
        "What licence category would apply, which application form is required, what are the major technical-personnel "
        "and manufacturing requirements, and which GMP requirements must the company satisfy?"
    )
    req = QueryRequest(raw_query=query)
    res = coordinator.execute(req)

    assert res.is_abstention is False
    answer_text = res.answer.lower()
    
    # Assert key legal distinctions and concepts
    assert "form 24" in answer_text or "24-d" in answer_text
    assert "licensing authority" in answer_text or "state" in answer_text
    assert "schedule t" in answer_text or "gmp" in answer_text
    assert "rule 158" in answer_text or "158-b" in answer_text
    assert "technical" in answer_text or "personnel" in answer_text or "qualified" in answer_text
    assert len(res.evidence) >= 1
    assert len(res.citations) >= 1


def test_ayurvedic_patentability_and_tkdl_role(coordinator):
    """TEST 2: Ayush formulation patentability, Section 3(p)/3(e), and accurate TKDL digital search tool role."""
    query = (
        "If a company develops a new Ayurvedic formulation using ingredients and therapeutic uses documented in "
        "traditional Indian medicine, what IP protection could potentially be considered, and how could TKDL affect patent examination?"
    )
    req = QueryRequest(raw_query=query)
    res = coordinator.execute(req)

    assert res.is_abstention is False
    answer_text = res.answer
    answer_lower = answer_text.lower()

    # Assert accurate TKDL and WIPO legal terminology
    assert "wipo rejects" not in answer_lower, "Response contained inaccurate 'WIPO rejects' claim."
    assert "tkdl itself is prior art" not in answer_lower, "Response contained inaccurate 'TKDL itself is prior art' claim."
    
    # Assert patentability criteria & Section 3 provisions
    assert "section 3" in answer_lower or "patentability" in answer_lower or "novelty" in answer_lower
    assert "tkdl" in answer_lower
    assert len(res.evidence) >= 1


def test_hindi_multilingual_commercial_ayurvedic_query(coordinator):
    """TEST 3: Hindi multilingual query on commercial Ayurvedic manufacturing and patent rules."""
    hindi_query = (
        "यदि कोई कंपनी भारत में किसी पारंपरिक आयुर्वेदिक औषधि को नए व्यावसायिक उत्पाद के रूप में बनाकर बेचने की योजना बना रही है, "
        "तो उसे पेटेंट और निर्माण लाइसेंस के लिए किन प्रमुख नियमों और आवश्यकताओं पर ध्यान देना चाहिए?"
    )
    req = QueryRequest(raw_query=hindi_query)
    res = coordinator.execute(req)

    assert res.is_abstention is False
    assert len(res.evidence) >= 1
    assert len(res.answer) > 50


def test_malayalam_multilingual_tkdl_prior_art_query(coordinator):
    """TEST 4: Malayalam multilingual query on TKDL role and patentability of traditional knowledge."""
    malayalam_query = (
        "പരമ്പരാഗത അറിവിൽ ഇതിനകം രേഖപ്പെടുത്തിയിട്ടുള്ള ഒരു ആയുർവേദ ഔഷധത്തിന് പുതിയൊരു പേറ്റന്റ് നേടാൻ ശ്രമിക്കുമ്പോൾ, "
        "പരമ്പരാഗത അറിവിന്റെ മുൻഗണനാ അവകാശങ്ങളും TKDL-ന്റെ പങ്കും എങ്ങനെ പരിഗണിക്കണം?"
    )
    req = QueryRequest(raw_query=malayalam_query)
    res = coordinator.execute(req)

    assert res.is_abstention is False
    assert len(res.evidence) >= 1
    assert len(res.answer) > 50


def test_safe_abstention_multi_jurisdiction_antarctica(coordinator):
    """TEST 5: Multi-jurisdictional query with unsupported jurisdiction (Antarctica) must safely abstain."""
    query = (
        "An Ayurvedic startup wants to register a patent for a new formulation simultaneously in India, "
        "the United States, Japan and Antarctica. What are the exact filing fees, forms, examination timelines "
        "and approval requirements in each jurisdiction as of 2026?"
    )
    req = QueryRequest(raw_query=query)
    res = coordinator.execute(req)

    assert res.is_abstention is True, "Multi-jurisdictional Antarctica fee query failed to abstain safely."
    assert res.confidence is None or res.confidence.below_threshold is True
