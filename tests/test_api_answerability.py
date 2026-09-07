"""
tests.test_api_answerability — Integration tests for FastAPI POST /query endpoint.

Verifies HTTP response schemas for out-of-domain and valid IP-SAKTI queries.
"""

import os
import pytest
from fastapi.testclient import TestClient

from ip_sakti.api.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env():
    os.environ["HF_HUB_OFFLINE"] = "1"


@pytest.mark.parametrize(
    "invalid_query",
    [
        "who is manu",
        "what is the capital of France",
        "who is Elon Musk",
        "how do I repair my laptop",
        "tell me a joke",
        "xyzabc123",
    ],
)
def test_api_out_of_domain_queries_abstain(invalid_query: str) -> None:
    """HTTP POST /query for out-of-domain queries must return is_abstention=True, confidence=None, evidence=[]."""
    payload = {"raw_query": invalid_query}
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_abstention"] is True
    assert data["confidence"] is None
    assert data["evidence"] == []
    assert "cannot provide" in data["answer"] or "insufficient" in data["answer"] or "outside" in data["answer"]


@pytest.mark.parametrize(
    "valid_query",
    [
        "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?",
        "What are the licensing requirements under Rule 158-B for manufacturing Ayurvedic drugs?",
        "How does TKDL help prevent patents based on traditional Indian knowledge?",
        "What is Section 3(p) of the Indian Patents Act?",
    ],
)
def test_api_valid_queries_succeed(valid_query: str) -> None:
    """HTTP POST /query for valid queries must return is_abstention=False and evidence chunks."""
    payload = {"raw_query": valid_query}
    resp = client.post("/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_abstention"] is False
    assert data["confidence"] is not None
    assert len(data["evidence"]) >= 1
    assert len(data["answer"]) > 50
