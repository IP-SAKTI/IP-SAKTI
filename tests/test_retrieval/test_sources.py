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
    assert registry.is_authorised_url("https://www.ipindia.gov.in/patents-act-1970.htm") is True
    assert registry.is_authorised_url("https://www.ayush.gov.in/docs/drugs-cosmetics-rules-158b.pdf") is True
    assert registry.is_authorised_url("https://www.randomunauthorizedwebsite.com/info") is False
