"""
ip_sakti.multilingual.translator — Translation component.

Handles translation between supported user languages and the internal
retrieval language (English).

Pipeline:

    User Language
          ↓
    English for RAG / LLM
          ↓
    English Answer
          ↓
    User Language

Citation markers such as [SOURCE_1] are preserved during translation.
"""

from __future__ import annotations

import logging
import re

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    NotValidPayload,
    RequestError,
    TranslationNotFound,
)

from ip_sakti.models.multilingual import TranslationResult
from ip_sakti.multilingual.exceptions import (
    TranslationError,
    UnsupportedLanguageError,
)
from ip_sakti.multilingual.language_registry import (
    LanguageRegistry,
    get_language_registry,
)

logger = logging.getLogger(__name__)


# Matches citation markers such as:
# [SOURCE_1]
# [SOURCE_2]
# [SOURCE_15]
_CITATION_PATTERN = re.compile(r"\[SOURCE_\d+\]")


class QueryTranslator:
    """
    Translates queries and responses between supported languages.

    English is used internally for:
        - retrieval
        - RAG
        - LLM synthesis

    User-facing responses are translated back to the detected language.
    """

    def __init__(
        self,
        registry: LanguageRegistry | None = None,
    ) -> None:
        """Initialise the translator."""

        self._registry = registry or get_language_registry()

        logger.debug(
            "QueryTranslator initialised",
            extra={
                "retrieval_language": self._registry.retrieval_language,
                "supported_languages": sorted(
                    self._registry.supported_codes
                ),
            },
        )

    # ==================================================================
    # QUERY TRANSLATION
    # ==================================================================

    def translate_to_retrieval_language(
        self,
        text: str,
        source_language: str,
    ) -> TranslationResult:
        """
        Translate a user query into English.

        English is the internal retrieval language.
        """

        source = source_language.lower().strip()
        target = self._registry.retrieval_language

        self._validate_language(source)

        return self._translate(
            text=text,
            source_language=source,
            target_language=target,
        )

    # ==================================================================
    # RESPONSE TRANSLATION
    # ==================================================================

    def translate_response(
        self,
        text: str,
        target_language: str,
    ) -> TranslationResult:
        """
        Translate an English answer back into the user's language.

        Citation markers such as [SOURCE_1] are preserved.
        """

        source = self._registry.retrieval_language
        target = target_language.lower().strip()

        self._validate_language(target)

        return self._translate_response_with_citations(
            text=text,
            source_language=source,
            target_language=target,
        )

    # ==================================================================
    # LANGUAGE VALIDATION
    # ==================================================================

    def _validate_language(self, code: str) -> None:
        """Validate that the language is supported."""

        if code == self._registry.retrieval_language:
            return

        if not self._registry.is_supported(code):
            raise UnsupportedLanguageError(
                f"Language {code!r} is not supported by IP-SAKTI. "
                f"Supported languages: "
                f"{sorted(self._registry.supported_codes)}"
            )

    # ==================================================================
    # GENERAL TRANSLATION
    # ==================================================================

    def _translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Perform normal translation."""

        if source_language == target_language:
            return TranslationResult(
                source_language=source_language,
                target_language=target_language,
                original_text=text,
                translated_text=text,
                was_translated=False,
            )

        translated_text = self._call_google_translate(
            text=text,
            source=source_language,
            target=target_language,
        )

        return TranslationResult(
            source_language=source_language,
            target_language=target_language,
            original_text=text,
            translated_text=translated_text,
            was_translated=True,
        )

    # ==================================================================
    # RESPONSE TRANSLATION WITH CITATION PRESERVATION
    # ==================================================================

    def _translate_response_with_citations(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """
        Translate an answer while preserving [SOURCE_X] citations.

        Example:

            English:
            The required form is Form 24D [SOURCE_1].

        becomes approximately:

            Hindi:
            आवश्यक फॉर्म 24D है [SOURCE_1]।
        """

        if source_language == target_language:
            return TranslationResult(
                source_language=source_language,
                target_language=target_language,
                original_text=text,
                translated_text=text,
                was_translated=False,
            )

        # --------------------------------------------------------------
        # Extract citation markers
        # --------------------------------------------------------------

        citations: list[str] = []

        def replace_citation(match: re.Match[str]) -> str:
            index = len(citations)
            citations.append(match.group(0))

            # Use a simple placeholder that Google Translate should leave
            # untouched.
            return f" CITATIONPLACEHOLDER{index} "

        protected_text = _CITATION_PATTERN.sub(
            replace_citation,
            text,
        )

        # --------------------------------------------------------------
        # Translate the natural language
        # --------------------------------------------------------------

        translated_text = self._call_google_translate(
            text=protected_text,
            source=source_language,
            target=target_language,
        )

        # --------------------------------------------------------------
        # Restore citations
        # --------------------------------------------------------------

        for index, citation in enumerate(citations):
            placeholder_pattern = re.compile(
                rf"\s*CITATIONPLACEHOLDER\s*{index}\s*",
                re.IGNORECASE,
            )

            translated_text = placeholder_pattern.sub(
                f" {citation} ",
                translated_text,
            )

        # Safety fallback:
        # If the translator altered the placeholder, restore citations
        # based on their original order.
        for index, citation in enumerate(citations):
            if citation not in translated_text:
                logger.warning(
                    "Citation placeholder was altered during translation",
                    extra={
                        "citation": citation,
                        "index": index,
                    },
                )

                translated_text = translated_text.replace(
                    f"CITATIONPLACEHOLDER{index}",
                    citation,
                )

        translated_text = re.sub(
            r"[ \t]+",
            " ",
            translated_text,
        ).strip()

        return TranslationResult(
            source_language=source_language,
            target_language=target_language,
            original_text=text,
            translated_text=translated_text,
            was_translated=True,
        )

    # ==================================================================
    # GOOGLE TRANSLATE
    # ==================================================================

    @staticmethod
    def _call_google_translate(
        text: str,
        source: str,
        target: str,
    ) -> str:
        """
        Call Google Translate through deep-translator.
        """

        try:
            translator = GoogleTranslator(
                source=source,
                target=target,
            )

            result = translator.translate(text)

            if result is None:
                raise TranslationError(
                    f"GoogleTranslator returned no translation "
                    f"for {source!r} → {target!r}."
                )

            translated_text = str(result).strip()

            if not translated_text:
                raise TranslationError(
                    f"GoogleTranslator returned an empty translation "
                    f"for {source!r} → {target!r}."
                )

            return translated_text

        except (
            LanguageNotSupportedException,
            NotValidPayload,
            RequestError,
            TranslationNotFound,
        ) as exc:

            logger.error(
                "Google translation failed",
                extra={
                    "source_language": source,
                    "target_language": target,
                    "error": str(exc),
                },
            )

            raise TranslationError(
                f"Translation failed "
                f"({source!r} → {target!r}): {exc}"
            ) from exc

        except TranslationError:
            raise

        except Exception as exc:

            logger.error(
                "Unexpected translation error",
                extra={
                    "source_language": source,
                    "target_language": target,
                    "error": str(exc),
                },
            )

            raise TranslationError(
                f"Unexpected translation failure "
                f"({source!r} → {target!r}): {exc}"
            ) from exc