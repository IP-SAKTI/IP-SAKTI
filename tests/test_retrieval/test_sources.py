"""
tests/test_retrieval/test_sources.py — Unit tests for ip_sakti.retrieval.sources.

Tests that:
  - AuthorisedSource Pydantic model validates required fields
  - SourceRegistry loads config/sources.json correctly
  - list_sources() and get_source() work as expected
  - is_authorised_url() correctly identifies government domains
"""

from __future__ import annotations

from pathlib import Path
import pytest

from ip_sakti.retrieval.sources import AuthorisedSource, SourceRegistry


def test_authorised_source_model() -> None:
    source = AuthorisedSource(
        source_id="test_source",
        title="Test Source Title",
        organisation="Test Org",
        source_type="act",
        jurisdiction="india",
        url="https://www.ipindia.gov.in/test",
        document_title="Test Document Title",
        topic="ip",
    )
    assert source.source_id == "test_source"
    assert source.language == "en"
    assert source.authority_level == "statutory"


def test_source_registry_load() -> None:
    registry = SourceRegistry()
    sources = registry.list_sources()
    assert len(sources) >= 8

    source = registry.get_source("ip_india_patents_act_3p")
    assert source is not None
    assert source.organisation == "Office of the Controller General of Patents, Designs and Trade Marks"
    assert source.topic == "ip"


def test_is_authorised_url() -> None:
    registry = SourceRegistry()
    assert registry.is_authorised_url("https://ipindia.gov.in/acts/patent-act-1970/section-3") is True
    assert registry.is_authorised_url("https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/Drugs-Rules/") is True
    assert registry.is_authorised_url("https://www.randomunauthorizedwebsite.com/info") is False


def test_source_url_validation_audit() -> None:
    """Validate that all configured source external URLs pass structural & hostname checks."""
    registry = SourceRegistry()
    val_results = registry.validate_urls(check_network=False)
    assert len(val_results) >= 8

    for item in val_results:
        assert item["is_valid"] is True, f"URL validation failed for {item['source_id']}: {item['errors']}"
        assert not item["url"].startswith("http://localhost"), f"Localhost URL found for {item['source_id']}"
        assert "www.ipindia.gov.in" not in item["url"].lower(), f"Obsolete www.ipindia.gov.in host found in {item['source_id']}"


def test_specific_sources_urls() -> None:
    """Specifically test required source external URLs per requirements."""
    registry = SourceRegistry()

    # 1. Test ip_india_patents_act_3p URL
    patents_act_3p = registry.get_source("ip_india_patents_act_3p")
    assert patents_act_3p is not None
    assert patents_act_3p.url == "https://ipindia.gov.in/acts/patent-act-1970/section-3"
    assert patents_act_3p.canonical_url == "https://ipindia.gov.in/resource/patents-resources-act"
    assert patents_act_3p.archive_url is not None
    assert patents_act_3p.archive_url.startswith("https://web.archive.org/")

    # 2. Test ip_india_ayush_guidelines_2025 URL
    ayush_guidelines = registry.get_source("ip_india_ayush_guidelines_2025")
    assert ayush_guidelines is not None
    assert "ipindia.gov.in" in ayush_guidelines.url
    assert ayush_guidelines.canonical_url == "https://ipindia.gov.in/resource/patents-resources-guidelines"
    assert ayush_guidelines.archive_url is not None
    assert ayush_guidelines.archive_url.startswith("https://web.archive.org/")


def test_archive_url_model_validation() -> None:
    """Test that archive_url must start with https://web.archive.org/."""
    valid_source = AuthorisedSource(
        source_id="test_archive_valid",
        title="Test Title",
        organisation="Test Org",
        source_type="act",
        jurisdiction="india",
        url="https://ipindia.gov.in/test",
        archive_url="https://web.archive.org/web/12345/https://ipindia.gov.in/test",
        document_title="Test Doc Title",
        topic="ip",
    )
    assert valid_source.archive_url == "https://web.archive.org/web/12345/https://ipindia.gov.in/test"

    with pytest.raises(ValueError, match="archive_url must begin with 'https://web.archive.org/'"):
        AuthorisedSource(
            source_id="test_archive_invalid",
            title="Test Title",
            organisation="Test Org",
            source_type="act",
            jurisdiction="india",
            url="https://ipindia.gov.in/test",
            archive_url="https://malicious-site.com/snapshot",
            document_title="Test Doc Title",
            topic="ip",
        )


def test_source_viewer_data_archive_url() -> None:
    """Test get_source_viewer_data exposes archive_url and is_valid_archive_url."""
    registry = SourceRegistry()

    # Source with archive_url
    data_with_archive = registry.get_source_viewer_data("ip_india_patents_act_3p")
    assert data_with_archive is not None
    assert data_with_archive["archive_url"] is not None
    assert data_with_archive["archive_url"].startswith("https://web.archive.org/")
    assert data_with_archive["is_valid_archive_url"] is True

    # Source without archive_url
    data_without_archive = registry.get_source_viewer_data("ayush_rule_158b")
    assert data_without_archive is not None
    assert data_without_archive["archive_url"] is None
    assert data_without_archive["is_valid_archive_url"] is False


