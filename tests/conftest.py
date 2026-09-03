"""
tests/conftest.py — Shared pytest fixtures for IP-SAKTI Sahayak.

All fixtures here are available to every test module without explicit import.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest
import yaml

from ip_sakti.utils.config import reload_settings


# ---------------------------------------------------------------------------
# Temporary YAML config fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_settings_yaml(tmp_path: Path) -> Path:
    """
    Write a minimal valid settings.yaml into a temporary directory and
    return the path to the file.

    Config loader cache is cleared before and after the test.
    """
    cfg = {
        "app": {
            "name": "IP-SAKTI Test",
            "description": "Test instance",
            "version": "0.0.0-test",
            "disclaimer": "Test disclaimer.",
        },
        "logging": {"level": "DEBUG", "format": "text", "log_dir": str(tmp_path / "logs")},
        "paths": {
            "data_dir": str(tmp_path / "data"),
            "index_dir": str(tmp_path / "indexes"),
            "db_dir": str(tmp_path / "db"),
            "db_name": "test_ip_sakti.db",
        },
        "models": {
            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "cross_encoder_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "llm_provider": "gemini",
            "llm_model": "gemini-1.5-flash",
            "lang_detect_library": "langdetect",
            "lang_detect_min_confidence": 0.5,
        },
        "retrieval": {
            "faiss_top_k": 20,
            "bm25_top_k": 20,
            "rerank_top_k": 5,
            "rrf_k": 60,
        },
        "safety": {
            "confidence_threshold": 0.5,
            "min_evidence_chunks": 2,
        },
        "api": {"host": "0.0.0.0", "port": 8000, "workers": 1},
        "ui": {"api_base_url": "http://localhost:8000"},
        "formulation_categories": [],
        "jurisdictions": [],
        "knowledge_sources": [],
    }

    config_file = tmp_path / "settings.yaml"
    with config_file.open("w", encoding="utf-8") as fh:
        yaml.dump(cfg, fh, default_flow_style=False)

    # Populate cache with the test config, then yield the path
    reload_settings(str(config_file))

    yield config_file

    # Clear the cache after the test to avoid cross-test contamination
    from ip_sakti.utils.config import get_settings
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Temporary database path fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> Path:
    """Return a path inside a temp directory for an isolated SQLite database."""
    return tmp_path / "db" / "test_ip_sakti.db"


# ---------------------------------------------------------------------------
# Environment isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure that real .env values do not leak into tests.
    Strip known secrets from the environment for the duration of each test.
    """
    for var in ("GEMINI_API_KEY",):
        monkeypatch.delenv(var, raising=False)
