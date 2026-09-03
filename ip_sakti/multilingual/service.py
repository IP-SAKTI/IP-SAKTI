"""
ip_sakti.multilingual.service — Multilingual processing service.

``MultilingualService`` is the single entry point for the entire multilingual
layer.  It wires together:

1. Language detection     (``LanguageDetector``)
2. Query normalisation    (``QueryNormalizer``)
3. Query translation      (``QueryTranslator``)
4. Response translation   (``QueryTranslator``)

And produces a ``MultilingualContext`` that the Orchestrator consumes
(Stage 4).

Architecture reference (README.md §4):
  User → Language Detection → Multilingual Layer → Query Normalization
       → Orchestrator
"""

from __future__ import annotations

import logging
from uuid import UUID

from ip_sakti.models.multilingual import MultilingualContext
from ip_sakti.models.query import QueryRequest
from ip_sakti.multilingual.detector import LanguageDetector
from ip_sakti.multilingual.exceptions import (
    LanguageDetectionError,
    TranslationError,
    UnsupportedLanguageError,
)
from ip_sakti.multilingual.language_registry import LanguageRegistry, get_language_registry
from ip_sakti.multilingual.normalizer import QueryNormalizer
from ip_sakti.multilingual.translator import QueryTranslator

logger = logging.getLogger(__name__)


class MultilingualService:
    """
    Orchestrates the full multilingual processing pipeline for a single query.

    The service is stateless per-call; all heavy objects (registry, detector,
    normaliser, translator) are injected or constructed once and reused.

    Parameters
    ----------
    registry :
        Shared language registry.  Defaults to the cached singleton.
    detector :
        Language detector instance.  Constructed with defaults if not supplied.
    normalizer :
        Query normaliser instance.  Constructed with defaults if not supplied.
    translator :
        Query translator instance.  Constructed with defaults if not supplied.
    """

    def __init__(
        self,
        registry: LanguageRegistry | None = None,
        detector: LanguageDetector | None = None,
        normalizer: QueryNormalizer | None = None,
        translator: QueryTranslator | None = None,
    ) -> None:
        """Initialise with optional injected components (useful for testing)."""
        self._registry: LanguageRegistry = registry or get_language_registry()
        self._detector: LanguageDetector = detector or LanguageDetector(
            registry=self._registry
        )
        self._normalizer: QueryNormalizer = normalizer or QueryNormalizer()
        self._translator: QueryTranslator = translator or QueryTranslator(
            registry=self._registry
        )
        logger.debug("MultilingualService initialised")

    def process(self, request: QueryRequest) -> MultilingualContext:
        """
        Run the full multilingual pipeline for *request*.

        Steps
        -----
        1. If the user supplied an explicit ``user_language``, use it directly
           (skip detection).  Otherwise run the language detector.
        2. Normalise the raw query text.
        3. Translate the normalised query into the retrieval language (English).

        Parameters
        ----------
        request :
            The incoming ``QueryRequest`` from the Streamlit UI or API.

        Returns
        -------
        MultilingualContext
            The complete multilingual metadata for this query.  Feed this
            into the Orchestrator.

        Raises
        ------
        LanguageDetectionError
            If automatic detection fails and no user_language was supplied.
        TranslationError
            If translation to the retrieval language fails.
        UnsupportedLanguageError
            If an explicitly supplied ``user_language`` is not in the registry.
        """
        logger.info(
            "Processing multilingual context",
            extra={"query_id": str(request.query_id)},
        )

        # ── Step 1: Language detection ────────────────────────────────────────
        if request.user_language:
            lang_code = request.user_language.lower()
            if (
                lang_code != self._registry.retrieval_language
                and not self._registry.is_supported(lang_code)
            ):
                raise UnsupportedLanguageError(
                    f"User-supplied language {lang_code!r} is not in the "
                    "supported language registry."
                )
            from ip_sakti.models.multilingual import DetectionResult
            detection = DetectionResult(
                language=lang_code,
                confidence=1.0,
                is_fallback=False,
            )
            logger.debug(
                "Using user-supplied language",
                extra={"language": lang_code},
            )
        else:
            detection = self._detector.detect(request.raw_query)

        effective_language = detection.language

        # ── Step 2: Normalisation ─────────────────────────────────────────────
        normalisation = self._normalizer.normalise(request.raw_query)

        # ── Step 3: Query translation ─────────────────────────────────────────
        query_translation = self._translator.translate_to_retrieval_language(
            text=normalisation.normalised,
            source_language=effective_language,
        )

        context = MultilingualContext(
            query_id=request.query_id,
            raw_query=request.raw_query,
            detection=detection,
            normalisation=normalisation,
            query_translation=query_translation,
            response_translation=None,
            effective_language=effective_language,
        )

        logger.info(
            "Multilingual context assembled",
            extra={
                "query_id": str(request.query_id),
                "detected_language": effective_language,
                "was_translated": query_translation.was_translated,
            },
        )
        return context

    def translate_response(
        self,
        response_text: str,
        context: MultilingualContext,
    ) -> MultilingualContext:
        """
        Translate a generated English response back to the user's language.

        This is called after LLM answer generation (Stage 5).  It returns an
        updated ``MultilingualContext`` with ``response_translation`` populated.

        Parameters
        ----------
        response_text :
            The English answer text produced by the LLM pipeline.
        context :
            The ``MultilingualContext`` produced earlier by ``process()``.

        Returns
        -------
        MultilingualContext
            A new instance with ``response_translation`` set.

        Raises
        ------
        TranslationError
            If translation back to the user's language fails.
        """
        response_translation = self._translator.translate_response(
            text=response_text,
            target_language=context.effective_language,
        )

        logger.debug(
            "Response translated",
            extra={
                "query_id": str(context.query_id),
                "target_language": context.effective_language,
                "was_translated": response_translation.was_translated,
            },
        )

        # Return a new context with response_translation filled in.
        return context.model_copy(
            update={"response_translation": response_translation}
        )
