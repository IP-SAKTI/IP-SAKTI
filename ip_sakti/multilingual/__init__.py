"""
ip_sakti.multilingual — Language detection, translation, and normalisation.

Public API
----------
    from ip_sakti.multilingual import (
        MultilingualService,
        LanguageDetector,
        QueryNormalizer,
        QueryTranslator,
        LanguageRegistry,
        get_language_registry,
        reload_language_registry,
        LanguageDetectionError,
        TranslationError,
        UnsupportedLanguageError,
    )
"""

from ip_sakti.multilingual.detector import LanguageDetector
from ip_sakti.multilingual.exceptions import (
    LanguageDetectionError,
    TranslationError,
    UnsupportedLanguageError,
)
from ip_sakti.multilingual.language_registry import (
    LanguageRegistry,
    get_language_registry,
    reload_language_registry,
)
from ip_sakti.multilingual.normalizer import QueryNormalizer
from ip_sakti.multilingual.service import MultilingualService
from ip_sakti.multilingual.translator import QueryTranslator

__all__ = [
    "LanguageDetectionError",
    "LanguageDetector",
    "LanguageRegistry",
    "MultilingualService",
    "QueryNormalizer",
    "QueryTranslator",
    "TranslationError",
    "UnsupportedLanguageError",
    "get_language_registry",
    "reload_language_registry",
]
