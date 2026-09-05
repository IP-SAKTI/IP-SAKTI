"""
ip_sakti.multilingual.detector — Language detection component.

Uses the ``langdetect`` library (pretrained statistical model) to identify
the language of the user's query text.

Approved per AGENTS.md §5: "Language detection: Use ``langdetect`` or
``lingua`` (pretrained)."

Design decisions
----------------
- ``langdetect.detect_langs()`` is used instead of ``detect()`` because it
  returns a ranked list of (language, probability) pairs, allowing the caller
  to inspect confidence.
- ``DetectorFactory.seed(0)`` is called once at import time to make detection
  deterministic (important for testing and reproducibility).
- If the top result's confidence is below ``lang_detect_min_confidence`` from
  ``config/settings.yaml``, the fallback language (``"en"``) is returned with
  ``DetectionResult.is_fallback = True``.
- Any ``LangDetectException`` is re-raised as ``LanguageDetectionError``.
"""

from __future__ import annotations

import logging

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

from ip_sakti.models.multilingual import DetectionResult
from ip_sakti.multilingual.exceptions import LanguageDetectionError
from ip_sakti.multilingual.language_registry import LanguageRegistry, get_language_registry
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)

# Seed the detector once at import time for deterministic results.
DetectorFactory.seed = 0


class LanguageDetector:
    """
    Detects the language of an input text using ``langdetect``.

    Parameters
    ----------
    registry :
        The language registry used to look up the fallback language.
        Defaults to the shared singleton from ``get_language_registry()``.
    min_confidence :
        Minimum detection confidence (0.0–1.0) before the fallback language
        is used instead.  Loaded from ``models.lang_detect_min_confidence``
        in ``settings.yaml`` when not supplied.
    """

    def __init__(
        self,
        registry: LanguageRegistry | None = None,
        min_confidence: float | None = None,
    ) -> None:
        """Initialise the detector with optional registry and threshold."""
        self._registry: LanguageRegistry = registry or get_language_registry()

        if min_confidence is not None:
            self._min_confidence = float(min_confidence)
        else:
            cfg = get_settings()
            self._min_confidence = float(
                cfg.get("models", {}).get("lang_detect_min_confidence", 0.5)
            )

        logger.debug(
            "LanguageDetector initialised",
            extra={"min_confidence": self._min_confidence},
        )

    def detect(self, text: str) -> DetectionResult:
        """
        Detect the language of *text*.

        Parameters
        ----------
        text :
            The raw query string submitted by the user.  Must be non-empty.

        Returns
        -------
        DetectionResult
            Contains the detected ISO 639-1 language code, confidence, and
            a flag indicating whether the fallback language was used.

        Raises
        ------
        LanguageDetectionError
            If *text* is empty, or if ``langdetect`` cannot produce any result.
        """
        stripped = text.strip()
        if not stripped:
            raise LanguageDetectionError(
                "Language detection failed: input text is empty."
            )

        try:
            candidates = detect_langs(stripped)
        except LangDetectException as exc:
            raise LanguageDetectionError(
                f"Language detection failed for input {stripped[:50]!r}: {exc}"
            ) from exc

        if not candidates:
            raise LanguageDetectionError(
                "Language detection returned no candidates."
            )

        top = candidates[0]
        detected_lang: str = top.lang
        confidence: float = float(top.prob)

        if (
            confidence < self._min_confidence
            or not self._registry.is_supported(detected_lang)
        ):
            fallback = self._registry.fallback_language
            logger.info(
                "Detection confidence below threshold or language unsupported; using fallback",
                extra={
                    "detected": detected_lang,
                    "confidence": confidence,
                    "threshold": self._min_confidence,
                    "is_supported": self._registry.is_supported(detected_lang),
                    "fallback": fallback,
                },
            )
            return DetectionResult(
                language=fallback,
                confidence=confidence,
                is_fallback=True,
            )

        logger.debug(
            "Language detected",
            extra={"language": detected_lang, "confidence": confidence},
        )
        return DetectionResult(
            language=detected_lang,
            confidence=confidence,
            is_fallback=False,
        )
