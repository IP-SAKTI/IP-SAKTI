"""
tests/test_document_endpoint.py — Tests for GET /document/{source_id} API endpoint.

Verifies:
  - Valid source_id returns HTTP 302 redirect to canonical URL
  - Unknown source_id returns HTTP 404
  - Path traversal attempts are safely rejected (404)
  - Correct response headers

Uses an isolated FastAPI test app that only registers the /document route,
avoiding the full IPSAKTIService / embedding model initialization.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from ip_sakti.retrieval.sources import SourceRegistry


# ---------------------------------------------------------------------------
# Minimal test app — registers only the /document route
# ---------------------------------------------------------------------------

def _build_test_app() -> FastAPI:
    """Build an isolated FastAPI app with just the document endpoint."""
    _app = FastAPI()
    _registry = SourceRegistry()

    @_app.get("/document/{source_id}")
    async def get_source_document(source_id: str) -> RedirectResponse:
        source_meta = _registry.get_source(source_id)
        if source_meta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source document '{source_id}' not found in the knowledge registry.",
            )
        canonical_url = source_meta.url
        if not canonical_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No URL available for source '{source_id}'.",
            )
        return RedirectResponse(url=canonical_url, status_code=302)

    return _app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return a TestClient for the isolated document endpoint app."""
    return TestClient(_build_test_app(), follow_redirects=False)


class TestDocumentEndpoint:
    """Tests for GET /document/{source_id}."""

    def test_valid_source_id_returns_redirect(self, client: TestClient) -> None:
        """A known source_id must return 302 redirect to the canonical URL."""
        response = client.get("/document/ayush_rule_158b")
        assert response.status_code == 302
        location = response.headers.get("location", "")
        assert location.startswith("http"), (
            f"Expected HTTP redirect URL, got: {location!r}"
        )

    def test_valid_ip_source_returns_redirect(self, client: TestClient) -> None:
        """Another known source_id (ip_india_patents_act_3p) returns 302."""
        response = client.get("/document/ip_india_patents_act_3p")
        assert response.status_code == 302

    def test_unknown_source_id_returns_404(self, client: TestClient) -> None:
        """An unregistered source_id must return 404 Not Found."""
        response = client.get("/document/does_not_exist_xyz")
        assert response.status_code == 404

    def test_path_traversal_encoded_returns_404(self, client: TestClient) -> None:
        """URL-encoded path traversal attempt must not expose the filesystem."""
        # The source_id 'etc/passwd' will not be in the registry → 404
        response = client.get("/document/etc%2Fpasswd")
        assert response.status_code in (404, 422)
        if response.status_code == 302:
            location = response.headers.get("location", "")
            # Must not be a filesystem path
            assert not location.startswith("/etc/"), (
                "Path traversal succeeded — security vulnerability!"
            )

    def test_path_traversal_dotdot_not_in_registry(self, client: TestClient) -> None:
        """.. traversal source_id is not in registry → 404."""
        # The raw string '../config/settings.yaml' is not a valid source_id
        response = client.get("/document/..config.settings")
        assert response.status_code == 404

    def test_redirect_location_is_https_url(self, client: TestClient) -> None:
        """The redirect Location must be an HTTP/HTTPS URL, not a filesystem path."""
        response = client.get("/document/biodiversity_act_2002")
        assert response.status_code == 302
        location = response.headers.get("location", "")
        assert location.startswith("https://") or location.startswith("http://"), (
            f"Expected HTTPS redirect URL, got: {location!r}"
        )

    def test_wipo_source_redirects_to_wipo_int(self, client: TestClient) -> None:
        """WIPO TKDL source redirects to wipo.int."""
        response = client.get("/document/tkdl_wipo_policy")
        assert response.status_code == 302
        location = response.headers.get("location", "")
        assert "wipo.int" in location

    def test_nba_source_redirects_to_nbaindia(self, client: TestClient) -> None:
        """NBA ABS source redirects to nbaindia.org."""
        response = client.get("/document/nba_abs_regulations_2014")
        assert response.status_code == 302
        location = response.headers.get("location", "")
        assert "nbaindia.org" in location

    def test_all_registered_sources_are_redirectable(self, client: TestClient) -> None:
        """Every registered source_id must return a valid 302 redirect."""
        registry = SourceRegistry()
        for source in registry.list_sources():
            resp = client.get(f"/document/{source.source_id}")
            assert resp.status_code == 302, (
                f"source_id={source.source_id!r} returned {resp.status_code}, expected 302"
            )
            loc = resp.headers.get("location", "")
            assert loc.startswith("http"), (
                f"source_id={source.source_id!r} has non-HTTP redirect: {loc!r}"
            )
