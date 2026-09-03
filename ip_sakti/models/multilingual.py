"""
ip_sakti.models.multilingual — Pydantic v2 models for the multilingual layer.

These models carry the outputs of each sub-component through the pipeline:
  Language Detection → Multilingual Layer → Query Normalization

The ``MultilingualContext`` produced here feeds into ``QueryContext``
(defined in ip_sakti.models.query) when the Orchestrator is assembled in
Stage 4.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """
    Result returned by the language detector.

    Attributes
    ----------
    language :
        ISO 639-1 language code of the detected language, e.g. ``"hi"``.
    confidence :
        Probability/confidence score produced by the detector (0.0–1.0).
    is_fallback :
        ``True`` when the detector's confidence was below the configured
        threshold and the ``fallback_language`` was used instead.
    """

    language: str = Field(
        ...,
        description="ISO 639-1 code of the detected (or fallback) language.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence reported by langdetect (0.0–1.0).",
    )
    is_fallback: bool = Field(
        default=False,
        description=(
            "True if the system fell back to the fallback language because "
            "detection confidence was below the configured threshold."
        ),
    )


class NormalisationResult(BaseModel):
    """
    Result returned by the query normaliser.

    Attributes
    ----------
    original :
        The raw query string before any normalisation.
    normalised :
        The query after all normalisation steps have been applied.
    transformations :
        Human-readable list of transformations applied, e.g.
        ``["nfc", "whitespace_collapse", "ayurveda_terms"]``.
        Empty if the query required no changes.
    """

    original: str = Field(
        ...,
        description="Raw query text before normalisation.",
    )
    normalised: str = Field(
        ...,
        description="Query text after all normalisation steps.",
    )
    transformations: list[str] = Field(
        default_factory=list,
        description="Ordered list of normalisation steps that changed the text.",
    )


class TranslationResult(BaseModel):
    """
    Result returned by the query translator.

    Attributes
    ----------
    source_language :
        ISO 639-1 code of the source language.
    target_language :
        ISO 639-1 code of the target language.
    original_text :
        Text before translation.
    translated_text :
        Text after translation (equals ``original_text`` when
        ``was_translated`` is ``False``).
    was_translated :
        ``False`` when translation was skipped because source == target.
    """

    source_language: str = Field(
        ...,
        description="ISO 639-1 source language code.",
    )
    target_language: str = Field(
        ...,
        description="ISO 639-1 target language code.",
    )
    original_text: str = Field(
        ...,
        description="Text before translation.",
    )
    translated_text: str = Field(
        ...,
        description=(
            "Translated text. Equals original_text when was_translated is False."
        ),
    )
    was_translated: bool = Field(
        default=True,
        description=(
            "False when translation was skipped because source and target "
            "languages are the same."
        ),
    )


class MultilingualContext(BaseModel):
    """
    Complete output of the multilingual processing layer for one query.

    Produced by ``MultilingualService.process()`` and passed directly
    to the Orchestrator in Stage 4.

    Attributes
    ----------
    query_id :
        UUID matching the originating ``QueryRequest``.
    raw_query :
        The original, unmodified query text submitted by the user.
    detection :
        Language detection result.
    normalisation :
        Query normalisation result.
    query_translation :
        Translation of the normalised query into the retrieval language.
    response_translation :
        Translation of a generated response back to the user's language.
        ``None`` until the response has been generated (Stage 5+).
    effective_language :
        The language code that the rest of the pipeline will treat as the
        user's language.  Usually equals ``detection.language`` unless the
        user supplied an explicit override via ``QueryRequest.user_language``.
    """

    query_id: UUID = Field(
        ...,
        description="Matches the originating QueryRequest.query_id.",
    )
    raw_query: str = Field(
        ...,
        description="Original user query text, unmodified.",
    )
    detection: DetectionResult = Field(
        ...,
        description="Output of the language detector.",
    )
    normalisation: NormalisationResult = Field(
        ...,
        description="Output of the query normaliser.",
    )
    query_translation: TranslationResult = Field(
        ...,
        description="Translation of the normalised query into the retrieval language.",
    )
    response_translation: TranslationResult | None = Field(
        default=None,
        description=(
            "Translation of the generated answer back to the user's language. "
            "Populated in Stage 5 after answer generation."
        ),
    )
    effective_language: str = Field(
        ...,
        description=(
            "The language code the pipeline uses as the user's language. "
            "Usually detection.language; overridden by QueryRequest.user_language "
            "if the user supplied one explicitly."
        ),
    )
