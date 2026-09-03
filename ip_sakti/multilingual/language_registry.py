"""
ip_sakti.multilingual.language_registry — Supported-language registry.

Loads the supported language list from ``config/languages.yaml`` (resolved
relative to the project root) and exposes a lightweight query interface.

All other multilingual modules should use this registry rather than
hard-coding language codes.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ip_sakti.multilingual.exceptions import UnsupportedLanguageError

logger = logging.getLogger(__name__)

# Path to the languages config file relative to the repository root.
# Resolved from this file's location: ip_sakti/multilingual/ → ../../config/
_LANGUAGES_YAML_PATH = (
    Path(__file__).parent.parent.parent / "config" / "languages.yaml"
)


def _load_languages_yaml(path: Path) -> dict[str, Any]:
    """Read and parse languages.yaml, returning the raw dict."""
    if not path.exists():
        raise FileNotFoundError(
            f"Languages configuration not found: {path}. "
            "Ensure config/languages.yaml exists in the repository root."
        )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or {}


class LanguageRegistry:
    """
    In-memory registry of languages supported by the IP-SAKTI multilingual layer.

    Loaded once from ``config/languages.yaml``.  All language code comparisons
    are case-insensitive and normalised to lowercase.

    Attributes
    ----------
    retrieval_language : str
        The internal processing language (always ``"en"`` per configuration).
    fallback_language : str
        The language used when detection confidence is too low.
    supported_codes : frozenset[str]
        ISO 639-1 codes of all configured languages.
    """

    def __init__(self, yaml_path: Path | None = None) -> None:
        """
        Initialise the registry by loading languages.yaml.

        Parameters
        ----------
        yaml_path :
            Override path to the languages YAML file.  Defaults to
            ``config/languages.yaml`` at the repository root.
        """
        path = yaml_path or _LANGUAGES_YAML_PATH
        raw = _load_languages_yaml(path)

        self._languages: dict[str, dict[str, str]] = {
            entry["code"].lower(): entry
            for entry in raw.get("supported_languages", [])
        }
        self.retrieval_language: str = raw.get("retrieval_language", "en").lower()
        self.fallback_language: str = raw.get("fallback_language", "en").lower()
        self.supported_codes: frozenset[str] = frozenset(self._languages.keys())

        logger.debug(
            "LanguageRegistry loaded",
            extra={
                "num_languages": len(self._languages),
                "retrieval_language": self.retrieval_language,
                "fallback_language": self.fallback_language,
            },
        )

    def is_supported(self, code: str) -> bool:
        """
        Return ``True`` if *code* is a configured supported language.

        Parameters
        ----------
        code :
            ISO 639-1 language code (case-insensitive).
        """
        return code.lower() in self.supported_codes

    def get_language_info(self, code: str) -> dict[str, str]:
        """
        Return the metadata dict for a language code.

        Parameters
        ----------
        code :
            ISO 639-1 language code (case-insensitive).

        Returns
        -------
        dict[str, str]
            Keys: ``code``, ``name``, ``script``, ``region``.

        Raises
        ------
        UnsupportedLanguageError
            If *code* is not in the supported language list.
        """
        key = code.lower()
        if key not in self._languages:
            raise UnsupportedLanguageError(
                f"Language code {code!r} is not configured in languages.yaml. "
                f"Supported codes: {sorted(self.supported_codes)}"
            )
        return dict(self._languages[key])

    def __len__(self) -> int:
        """Return the number of supported languages."""
        return len(self._languages)


@lru_cache(maxsize=1)
def get_language_registry(yaml_path: str | None = None) -> LanguageRegistry:
    """
    Return a cached singleton ``LanguageRegistry``.

    Parameters
    ----------
    yaml_path :
        Optional override path (as string) to the languages YAML file.
        Pass ``None`` to use the default project-root location.

    Returns
    -------
    LanguageRegistry
        The shared registry instance.
    """
    path = Path(yaml_path) if yaml_path else None
    return LanguageRegistry(yaml_path=path)


def reload_language_registry(yaml_path: str | None = None) -> LanguageRegistry:
    """
    Clear the registry cache and reload from disk.

    Intended for use in tests where the config path changes between test cases.
    """
    get_language_registry.cache_clear()
    return get_language_registry(yaml_path)
