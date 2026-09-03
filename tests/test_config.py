"""
tests/test_config.py — Unit tests for ip_sakti.utils.config.

Tests that the YAML config loader:
  - reads a valid YAML file correctly
  - exposes required top-level sections
  - applies environment-variable overrides
  - raises FileNotFoundError for a missing file
  - returns cached results on repeated calls
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ip_sakti.utils.config import get_settings, reload_settings


class TestConfigLoader:
    """Tests for get_settings() and reload_settings()."""

    def test_loads_valid_yaml(self, tmp_settings_yaml: Path) -> None:
        """Config loads without error from a valid YAML file."""
        cfg = reload_settings(str(tmp_settings_yaml))
        assert isinstance(cfg, dict)

    def test_required_sections_present(self, tmp_settings_yaml: Path) -> None:
        """All required top-level sections are present in the loaded config."""
        cfg = reload_settings(str(tmp_settings_yaml))
        required_sections = {
            "app", "logging", "paths", "models", "retrieval", "safety", "api",
        }
        for section in required_sections:
            assert section in cfg, f"Missing required config section: {section!r}"

    def test_app_metadata(self, tmp_settings_yaml: Path) -> None:
        """app.name and app.version are populated."""
        cfg = reload_settings(str(tmp_settings_yaml))
        assert cfg["app"]["name"] == "IP-SAKTI Test"
        assert cfg["app"]["version"] == "0.0.0-test"

    def test_model_names_present(self, tmp_settings_yaml: Path) -> None:
        """Approved model names are recorded in the config."""
        cfg = reload_settings(str(tmp_settings_yaml))
        assert cfg["models"]["embedding_model"] == (
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        assert cfg["models"]["cross_encoder_model"] == (
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        assert cfg["models"]["llm_provider"] == "gemini"

    def test_retrieval_defaults(self, tmp_settings_yaml: Path) -> None:
        """Retrieval parameters are present and of the correct type."""
        cfg = reload_settings(str(tmp_settings_yaml))
        assert isinstance(cfg["retrieval"]["faiss_top_k"], int)
        assert isinstance(cfg["retrieval"]["bm25_top_k"], int)
        assert isinstance(cfg["retrieval"]["rerank_top_k"], int)
        assert isinstance(cfg["retrieval"]["rrf_k"], int)

    def test_safety_threshold_in_range(self, tmp_settings_yaml: Path) -> None:
        """Confidence threshold is a float between 0 and 1."""
        cfg = reload_settings(str(tmp_settings_yaml))
        threshold = cfg["safety"]["confidence_threshold"]
        assert isinstance(threshold, (float, int))
        assert 0.0 <= float(threshold) <= 1.0

    def test_env_override_log_level(
        self, tmp_settings_yaml: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """LOG_LEVEL env var overrides the YAML logging.level value."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        cfg = reload_settings(str(tmp_settings_yaml))
        assert cfg["logging"]["level"] == "DEBUG"

    def test_env_override_rerank_top_k(
        self, tmp_settings_yaml: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RERANK_TOP_K env var overrides retrieval.rerank_top_k as int."""
        monkeypatch.setenv("RERANK_TOP_K", "10")
        cfg = reload_settings(str(tmp_settings_yaml))
        assert cfg["retrieval"]["rerank_top_k"] == 10

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError is raised for a non-existent settings file."""
        missing = tmp_path / "does_not_exist.yaml"
        with pytest.raises(FileNotFoundError, match="does_not_exist.yaml"):
            reload_settings(str(missing))

    def test_cache_returns_same_object(self, tmp_settings_yaml: Path) -> None:
        """Calling get_settings() twice returns the same cached dict."""
        cfg1 = reload_settings(str(tmp_settings_yaml))
        cfg2 = get_settings(str(tmp_settings_yaml))
        assert cfg1 is cfg2
