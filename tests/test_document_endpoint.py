"""
tests/test_document_endpoint.py — Tests for GET /document/{source_id} API endpoint.

Verifies:
  - Valid source_id returns HTTP 200 with local PDF FileResponse (application/pdf)
  - doc_ prefixed source IDs resolve correctly to local PDF files
  - format=html override returns local HTML viewer
  - format=json override returns structured viewer dictionary
  - Unknown source_id returns HTTP 404
  - Path traversal attempts are safely rejected (404/422)
  - Security checks preserve authorised URL validation
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ip_sakti.api.main import app
from ip_sakti.retrieval.sources import SourceRegistry


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return a TestClient for the FastAPI app."""
    return TestClient(app, follow_redirects=False)


class TestDocumentEndpoint:
    """Tests for GET /document/{source_id}."""

    def test_valid_source_id_returns_local_pdf(self, client: TestClient) -> None:
        """A known source_id must return HTTP 200 with application/pdf FileResponse."""
        response = client.get("/document/ayush_rule_158b")
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "").lower()
        assert response.content.startswith(b"%PDF")

    def test_doc_prefixed_source_ids_return_local_pdf(self, client: TestClient) -> None:
        """Evidence chunk IDs with doc_ prefix must resolve cleanly to HTTP 200 PDF files."""
        test_ids = [
            "doc_ayush_rule_158b",
            "doc_ayush_form_24d",
            "doc_patents_act_3p",
            "doc_biodiversity_act_2002",
            "doc_nba_abs_regulations_2014",
            "doc_tkdl_wipo_policy",
        ]
        for source_id in test_ids:
            response = client.get(f"/document/{source_id}")
            assert response.status_code == 200, f"Failed for {source_id}: {response.status_code}"
            assert "application/pdf" in response.headers.get("content-type", "").lower()
            assert response.content.startswith(b"%PDF")

    def test_html_format_override(self, client: TestClient) -> None:
        """Adding ?format=html returns the HTML viewer page."""
        response = client.get("/document/ayush_rule_158b?format=html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "").lower()
        assert "Local Source Document Viewer" in response.text
        assert "Rule 158-B" in response.text

    def test_json_format_parameter(self, client: TestClient) -> None:
        """Adding ?format=json must return a structured JSON response."""
        response = client.get("/document/ayush_rule_158b?format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "").lower()
        data = response.json()
        assert data["source_id"] == "ayush_rule_158b"
        assert data["local_available"] is True
        assert "Rule 158-B" in data["content"]
        assert data["official_url"] == "https://www.ayush.gov.in/docs/asu-l-rules.pdf"

    def test_unknown_source_id_returns_404(self, client: TestClient) -> None:
        """An unregistered source_id must return 404 Not Found."""
        response = client.get("/document/does_not_exist_xyz")
        assert response.status_code == 404

    def test_path_traversal_encoded_returns_404(self, client: TestClient) -> None:
        """URL-encoded path traversal attempt must not expose the filesystem."""
        response = client.get("/document/etc%2Fpasswd")
        assert response.status_code in (404, 422)

    def test_path_traversal_dotdot_not_in_registry(self, client: TestClient) -> None:
        """.. traversal source_id is not in registry → 404."""
        response = client.get("/document/..config.settings")
        assert response.status_code == 404

    def test_wipo_source_contains_official_url(self, client: TestClient) -> None:
        """WIPO TKDL source contains wipo.int link."""
        response = client.get("/document/tkdl_wipo_policy?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "wipo.int" in data["official_url"]
        assert data["is_authorised_url"] is True

    def test_nba_source_contains_official_url(self, client: TestClient) -> None:
        """NBA ABS source contains nbaindia.org link."""
        response = client.get("/document/nba_abs_regulations_2014?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "nbaindia.org" in data["official_url"]
        assert data["is_authorised_url"] is True

    def test_all_registered_sources_have_viewer(self, client: TestClient) -> None:
        """Every registered source_id must return a valid 200 viewer response."""
        registry = SourceRegistry()
        for source in registry.list_sources():
            resp = client.get(f"/document/{source.source_id}?format=json")
            assert resp.status_code == 200, (
                f"source_id={source.source_id!r} returned {resp.status_code}, expected 200"
            )
            data = resp.json()
            assert data["official_url"].startswith("http")



