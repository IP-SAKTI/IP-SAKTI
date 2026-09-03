"""
ip_sakti.multilingual.translator — Translation component.

Translates text between the user's language and the internal retrieval
language (English) using ``deep-translator`` with the Google Translate
backend.

Approved per AGENTS.md §5: "Translation: Use ``deep-translator``,
``googletrans``, or an approved multilingual model."

Design decisions
----------------
- Translation is skipped (identity) when source == target language.
- Only languages present in ``LanguageRegistry.supported_codes`` are accepted
  for the user-facing direction.  The retrieval language (``"en"``) is always
  accepted regardless.
- Any exception from ``deep_translator`` is wrapped in ``TranslationError``
  so callers deal with one exception type.
- The ``GoogleTranslator`` is instantiated per call (stateless, thread-safe).
"""

from __future__ import annotations

import logging

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    NotValidPayload,
    RequestError,
    TranslationNotFound,
)

from ip_sakti.models.multilingual import TranslationResult
from ip_sakti.multilingual.exceptions import TranslationError, UnsupportedLanguageError
from ip_sakti.multilingual.language_registry import LanguageRegistry, get_language_registry

logger = logging.getLogger(__name__)

# deep-translator uses full language codes internally; its Google backend
# accepts the same ISO 639-1 codes that langdetect produces, with the
# exception of "zh-cn" / "zh-tw" variants.  For the MVP the supported
# language set is well within Google Translate's supported range.

_DEEP_TRANSLATOR_EXCEPTIONS = (
    LanguageNotSupportedException,
    NotValidPayload,
    RequestError,
    TranslationNotFound,
    Exception,          # catch-all for network/HTTP errors
)


class QueryTranslator:
    """
    Translates queries and responses between user and retrieval languages.

    Parameters
    ----------
    registry :
        The language registry.  Defaults to the shared singleton.
    """

    def __init__(self, registry: LanguageRegistry | None = None) -> None:
        """Initialise the translator with an optional language registry."""
        self._registry: LanguageRegistry = registry or get_language_registry()
        logger.debug(
            "QueryTranslator initialised",
            extra={"retrieval_language": self._registry.retrieval_language},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate_to_retrieval_language(
        self,
        text: str,
        source_language: str,
    ) -> TranslationResult:
        """
        Translate *text* from *source_language* into the retrieval language.

        The retrieval language is always ``"en"`` as configured in
        ``config/languages.yaml``.

        Parameters
        ----------
        text :
            The query text to translate.
        source_language :
            ISO 639-1 code of the source language (e.g. ``"hi"``).

        Returns
        -------
        TranslationResult
            ``was_translated`` is ``False`` when source == retrieval language.

        Raises
        ------
        UnsupportedLanguageError
            If *source_language* is not in the supported language registry
            and is not the retrieval language itself.
        TranslationError
            If the translation API call fails.
        """
        target = self._registry.retrieval_language
        source = source_language.lower()
        self._validate_language(source)
        return self._translate(text, source_language=source, target_language=target)

    def translate_response(
        self,
        text: str,
        target_language: str,
    ) -> TranslationResult:
        """
        Translate a generated English response back into *target_language*.

        Parameters
        ----------
        text :
            The English response text to translate.
        target_language :
            ISO 639-1 code of the target language (e.g. ``"hi"``).

        Returns
        -------
        TranslationResult
            ``was_translated`` is ``False`` when target == retrieval language.

        Raises
        ------
        UnsupportedLanguageError
            If *target_language* is not in the supported language registry
            and is not the retrieval language itself.
        TranslationError
            If the translation API call fails.
        """
        source = self._registry.retrieval_language
        target = target_language.lower()
        self._validate_language(target)
        return self._translate(text, source_language=source, target_language=target)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_language(self, code: str) -> None:
        """
        Raise ``UnsupportedLanguageError`` if *code* is not valid.

        The retrieval language (``"en"``) is always valid regardless of
        registry contents.
        """
        if (
            code != self._registry.retrieval_language
            and not self._registry.is_supported(code)
        ):
            raise UnsupportedLanguageError(
                f"Language {code!r} is not in the supported language registry. "
                f"Supported codes: {sorted(self._registry.supported_codes)}"
            )

    def _translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """
        Core translation logic.

        Skips the API call when source == target (identity path).
        """
        if source_language == target_language:
            logger.debug(
                "Translation skipped (same language)",
                extra={"language": source_language},
            )
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

        logger.debug(
            "Translation completed",
            extra={
                "source": source_language,
                "target": target_language,
            },
        )
        return TranslationResult(
            source_language=source_language,
            target_language=target_language,
            original_text=text,
            translated_text=translated_text,
            was_translated=True,
        )

    @staticmethod
    def _call_google_translate(text: str, source: str, target: str) -> str:
        """
        Call the GoogleTranslator backend and return the translated string.

        Raises
        ------
        TranslationError
            On any exception from ``deep_translator``.
        """
        try:
            translator = GoogleTranslator(source=source, target=target)
            result = translator.translate(text)
            if result is None:
                raise TranslationError(
                    f"GoogleTranslator returned None for source={source!r}, "
                    f"target={target!r}, text={text[:50]!r}"
                )
            return str(result)
        except _DEEP_TRANSLATOR_EXCEPTIONS as exc:
            # Re-raise only if it wasn't already a TranslationError
            if isinstance(exc, TranslationError):
                raise
            raise TranslationError(
                f"Translation failed ({source!r} → {target!r}): {exc}"
            ) from exc
