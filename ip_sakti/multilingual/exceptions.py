"""
ip_sakti.multilingual.exceptions — Custom exceptions for the multilingual layer.

Raised when language detection, translation, or language validation fails.
Callers should catch these rather than bare exceptions so that failure modes
remain explicit throughout the pipeline.
"""

from __future__ import annotations


class LanguageDetectionError(Exception):
    """
    Raised when language detection cannot produce any result.

    Typical causes:
    - Input text is empty or too short for the detector.
    - The detection library raises an internal error.
    """


class TranslationError(Exception):
    """
    Raised when a translation call fails.

    Typical causes:
    - Network failure calling the translation API.
    - The translation provider returns an error response.
    - Source or target language code is not accepted by the provider.
    """


class UnsupportedLanguageError(Exception):
    """
    Raised when a language code is not listed in config/languages.yaml.

    This is a validation-level error, distinct from a translation failure.
    """
