"""
tests/test_api/test_endpoints.py

FastAPI integration endpoint tests using TestClient.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ip_sakti.api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    def test_health_endpoint(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ip-sakti-sahayak"
        assert "version" in data

    def test_query_endpoint_success(self) -> None:
        payload = {
            "raw_query": "What are the Section 3(p) patent filing rules in India?",
            "jurisdiction": "india",
            "formulation_category": "classical",
            "user_language": "en",
        }
        response = client.post("/query", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "query_id" in data
        assert "answer" in data
        assert "is_abstention" in data
        assert isinstance(data["is_abstention"], bool)
        assert "disclaimer" in data

    def test_query_endpoint_empty_raw_query(self) -> None:
        payload = {
            "raw_query": "   ",
            "jurisdiction": "india",
        }
        response = client.post("/query", json=payload)
        assert response.status_code == 422

    def test_query_endpoint_missing_raw_query(self) -> None:
        payload = {
            "jurisdiction": "india",
        }
        response = client.post("/query", json=payload)
        assert response.status_code == 422
