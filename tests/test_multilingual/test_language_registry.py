"""
tests/test_multilingual/test_language_registry.py

Tests for ip_sakti.multilingual.language_registry.LanguageRegistry.

Covers:
- Valid supported codes from the real config/languages.yaml
- Unsupported codes raise UnsupportedLanguageError
- retrieval_language is "en"
- get_language_info returns correct metadata
- Registry length matches expected count
- reload_language_registry clears cache
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ip_sakti.multilingual.exceptions import UnsupportedLanguageError
from ip_sakti.multilingual.language_registry import (
    LanguageRegistry,
    get_language_registry,
    reload_language_registry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_registry_from_real_config() -> LanguageRegistry:
    """Use the real languages.yaml so we test actual project config."""
    return LanguageRegistry()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLanguageRegistry:
    """Tests using the real config/languages.yaml."""

    def test_english_is_supported(self) -> None:
        """'en' must always be in the supported language set."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("en")

    def test_hindi_is_supported(self) -> None:
        """'hi' (Hindi) must be supported."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("hi")

    def test_tamil_is_supported(self) -> None:
        """'ta' (Tamil) must be supported."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("ta")

    def test_bengali_is_supported(self) -> None:
        """'bn' (Bengali) must be supported."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("bn")

    def test_kannada_is_supported(self) -> None:
        """'kn' (Kannada) must be supported."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("kn")

    def test_malayalam_is_supported(self) -> None:
        """'ml' (Malayalam) must be supported."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("ml")

    def test_telugu_is_supported(self) -> None:
        """'te' (Telugu) must be supported."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("te")

    def test_unknown_code_not_supported(self) -> None:
        """An invented code 'zz' must not be supported."""
        registry = _build_registry_from_real_config()
        assert not registry.is_supported("zz")

    def test_is_supported_case_insensitive(self) -> None:
        """Language code lookup must be case-insensitive."""
        registry = _build_registry_from_real_config()
        assert registry.is_supported("EN")
        assert registry.is_supported("Hi")

    def test_retrieval_language_is_english(self) -> None:
        """retrieval_language must be 'en' per config."""
        registry = _build_registry_from_real_config()
        assert registry.retrieval_language == "en"

    def test_fallback_language_is_english(self) -> None:
        """fallback_language must be 'en' per config."""
        registry = _build_registry_from_real_config()
        assert registry.fallback_language == "en"

    def test_get_language_info_english(self) -> None:
        """get_language_info('en') returns a dict with required keys."""
        registry = _build_registry_from_real_config()
        info = registry.get_language_info("en")
        assert info["code"] == "en"
        assert info["name"] == "English"
        assert "script" in info
        assert "region" in info

    def test_get_language_info_hindi(self) -> None:
        """get_language_info('hi') returns Hindi metadata."""
        registry = _build_registry_from_real_config()
        info = registry.get_language_info("hi")
        assert info["name"] == "Hindi"
        assert info["script"] == "Devanagari"

    def test_get_language_info_unsupported_raises(self) -> None:
        """get_language_info for unknown code raises UnsupportedLanguageError."""
        registry = _build_registry_from_real_config()
        with pytest.raises(UnsupportedLanguageError, match="zz"):
            registry.get_language_info("zz")

    def test_supported_codes_is_frozenset(self) -> None:
        """supported_codes must be a frozenset."""
        registry = _build_registry_from_real_config()
        assert isinstance(registry.supported_codes, frozenset)

    def test_registry_has_at_least_14_languages(self) -> None:
        """There must be at least 14 languages (13 Indian + English)."""
        registry = _build_registry_from_real_config()
        assert len(registry) >= 14

    def test_len_matches_supported_codes(self) -> None:
        """len(registry) must equal len(registry.supported_codes)."""
        registry = _build_registry_from_real_config()
        assert len(registry) == len(registry.supported_codes)


class TestLanguageRegistryCustomYaml:
    """Tests using a custom minimal YAML to isolate behaviour."""

    def _minimal_yaml(self, tmp_path: Path) -> Path:
        data = {
            "supported_languages": [
                {"code": "en", "name": "English", "script": "Latin", "region": "International"},
                {"code": "hi", "name": "Hindi", "script": "Devanagari", "region": "India"},
            ],
            "retrieval_language": "en",
            "fallback_language": "en",
        }
        p = tmp_path / "languages.yaml"
        with p.open("w") as fh:
            yaml.dump(data, fh)
        return p

    def test_custom_registry_contains_only_declared_codes(self, tmp_path: Path) -> None:
        """A custom YAML with 2 languages produces a registry of size 2."""
        yaml_path = self._minimal_yaml(tmp_path)
        registry = LanguageRegistry(yaml_path=yaml_path)
        assert len(registry) == 2
        assert registry.is_supported("hi")
        assert not registry.is_supported("ta")

    def test_missing_yaml_raises_file_not_found(self, tmp_path: Path) -> None:
        """A non-existent YAML raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            LanguageRegistry(yaml_path=tmp_path / "does_not_exist.yaml")


class TestLanguageRegistrySingleton:
    """Tests for the cached singleton get_language_registry()."""

    def test_cache_returns_same_object(self) -> None:
        """Two calls to get_language_registry() return the same object."""
        r1 = get_language_registry()
        r2 = get_language_registry()
        assert r1 is r2

    def test_reload_returns_fresh_registry(self) -> None:
        """reload_language_registry() clears the cache and returns a new instance."""
        r1 = get_language_registry()
        reload_language_registry()   # clears cache
        r2 = get_language_registry() # creates a brand-new instance
        # r1 and r2 are different objects (cache was cleared)
        assert r1 is not r2
        # But r2 is equivalent in content
        assert r2.retrieval_language == r1.retrieval_language
