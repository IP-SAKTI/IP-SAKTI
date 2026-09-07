"""
tests.test_query_answerability — Answerability and out-of-domain query safety regression tests.

Verifies that out-of-domain / irrelevant / unsupported queries safely abstain
with is_abstention=True and no evidence passed to synthesis, while valid IP-SAKTI
domain queries return source-grounded answers.
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


@pytest.mark.parametrize(
    "invalid_query",
    [
        "who is manu",
        "what is the capital of France",
        "who is Elon Musk",
        "how do I repair my laptop",
        "tell me a joke",
        "xyzabc123",
        "What is the exact government fee for registering a new Ayurvedic patent in Antarctica?",
    ],
)
def test_out_of_domain_queries_abstain(coordinator, invalid_query):
    """Out-of-domain and nonsense queries must safely abstain."""
    req = QueryRequest(raw_query=invalid_query)
    res = coordinator.execute(req)

    assert res.is_abstention is True, f"Query '{invalid_query}' failed to abstain."
    assert "cannot provide" in res.answer or "insufficient" in res.answer or "outside" in res.answer
    assert len(res.evidence) == 0, f"Irrelevant evidence returned for query '{invalid_query}'"


@pytest.mark.parametrize(
    "valid_query",
    [
        "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?",
        "What are the licensing requirements under Rule 158-B for manufacturing Ayurvedic drugs?",
        "How does TKDL help prevent patents based on traditional Indian knowledge?",
        "What is Section 3(p) of the Indian Patents Act?",
    ],
)
def test_valid_domain_queries_succeed(coordinator, valid_query):
    """Valid IP-SAKTI domain queries must return source-grounded responses."""
    req = QueryRequest(raw_query=valid_query)
    res = coordinator.execute(req)

    assert res.is_abstention is False, f"Valid query '{valid_query}' abstained unexpectedly."
    assert res.confidence is not None
    assert res.confidence.below_threshold is False
    assert len(res.evidence) >= 1
    assert len(res.answer) > 50
