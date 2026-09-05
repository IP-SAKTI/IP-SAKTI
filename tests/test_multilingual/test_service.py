"""
tests/test_multilingual/test_service.py

Tests for ip_sakti.multilingual.service.MultilingualService.

Covers:
- process() on an English query (no translation)
- process() on a Hindi query (with mocked translation)
- process() preserves raw_query on the context
- process() with explicit user_language overrides detection
- process() with unsupported user_language raises UnsupportedLanguageError
- translate_response() populates response_translation on the context
- MultilingualContext fields are correctly typed
- Metadata (query_id, effective_language) preserved through pipeline
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from ip_sakti.models.multilingual import (
    DetectionResult,
    MultilingualContext,
    NormalisationResult,
    TranslationResult,
)
from ip_sakti.models.query import QueryRequest
from ip_sakti.multilingual.exceptions import UnsupportedLanguageError
from ip_sakti.multilingual.language_registry import LanguageRegistry
from ip_sakti.multilingual.normalizer import QueryNormalizer
from ip_sakti.multilingual.service import MultilingualService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry() -> LanguageRegistry:
    return LanguageRegistry()


@pytest.fixture()
def service(registry: LanguageRegistry) -> MultilingualService:
    """Service using real components (translator will be mocked per test)."""
    return MultilingualService(registry=registry)


def _make_request(query: str, lang: str | None = None) -> QueryRequest:
    return QueryRequest(raw_query=query, user_language=lang)


# ---------------------------------------------------------------------------
# English query (no network call needed)
# ---------------------------------------------------------------------------


class TestServiceEnglishQuery:
    def test_process_english_query(self, service: MultilingualService) -> None:
        """An English query is processed without calling the translation API."""
        request = _make_request(
            "What is the patent process for Ayurvedic drugs?", lang="en"
        )
        context = service.process(request)

        assert isinstance(context, MultilingualContext)
        assert context.effective_language == "en"
        assert context.query_translation.was_translated is False

    def test_process_preserves_raw_query(self, service: MultilingualService) -> None:
        """raw_query on the context must exactly match the input."""
        raw = "  patent filing   "
        request = _make_request(raw, lang="en")
        context = service.process(request)
        assert context.raw_query == raw

    def test_process_preserves_query_id(self, service: MultilingualService) -> None:
        """query_id on the context must match the QueryRequest query_id."""
        request = _make_request("patent query", lang="en")
        context = service.process(request)
        assert context.query_id == request.query_id

    def test_process_normalises_query(self, service: MultilingualService) -> None:
        """The normalisation step runs and normalisation result is populated."""
        request = _make_request("triphla  patent  filing", lang="en")
        context = service.process(request)
        assert isinstance(context.normalisation, NormalisationResult)
        # Whitespace should be collapsed
        assert "  " not in context.normalisation.normalised

    def test_process_detection_result_present(
        self, service: MultilingualService
    ) -> None:
        """DetectionResult is populated on the context."""
        request = _make_request("patent query in Ayurveda", lang="en")
        context = service.process(request)
        assert isinstance(context.detection, DetectionResult)
        assert context.detection.language == "en"

    def test_response_translation_none_before_llm(
        self, service: MultilingualService
    ) -> None:
        """response_translation is None until translate_response() is called."""
        request = _make_request("patent question", lang="en")
        context = service.process(request)
        assert context.response_translation is None


# ---------------------------------------------------------------------------
# Hindi query (translation mocked)
# ---------------------------------------------------------------------------


class TestServiceHindiQuery:
    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_process_hindi_with_explicit_lang(
        self, mock_gt_cls: MagicMock, service: MultilingualService
    ) -> None:
        """process() with user_language='hi' translates query to English."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "patent filing process in India"
        mock_gt_cls.return_value = mock_instance

        request = _make_request(
            "भारत में पेटेंट दाखिल करने की प्रक्रिया", lang="hi"
        )
        context = service.process(request)

        assert context.effective_language == "hi"
        assert context.query_translation.was_translated is True
        assert context.query_translation.source_language == "hi"
        assert context.query_translation.target_language == "en"

    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_process_tamil_with_explicit_lang(
        self, mock_gt_cls: MagicMock, service: MultilingualService
    ) -> None:
        """process() with user_language='ta' translates Tamil query."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "Ayurvedic patent information"
        mock_gt_cls.return_value = mock_instance

        request = _make_request(
            "ஆயுர்வேத காப்புரிமை தகவல்", lang="ta"
        )
        context = service.process(request)
        assert context.effective_language == "ta"
        assert context.query_translation.was_translated is True


# ---------------------------------------------------------------------------
# Unsupported language
# ---------------------------------------------------------------------------


class TestServiceUnsupportedLanguage:
    def test_unsupported_user_language_raises(
        self, service: MultilingualService
    ) -> None:
        """An unsupported user_language raises UnsupportedLanguageError."""
        request = _make_request("some query", lang="zz")
        with pytest.raises(UnsupportedLanguageError, match="zz"):
            service.process(request)

    def test_auto_detected_unsupported_language_falls_back_to_en(
        self, service: MultilingualService
    ) -> None:
        """Auto-detected unsupported language (e.g. 'de') falls back to 'en' without raising error."""
        request = _make_request("AYUSH licensing steps under Rule 158-B", lang=None)
        context = service.process(request)
        assert context.effective_language == "en"
        assert context.detection.is_fallback is True


# ---------------------------------------------------------------------------
# translate_response()
# ---------------------------------------------------------------------------


class TestServiceTranslateResponse:
    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_translate_response_en_to_hi(
        self, mock_gt_cls: MagicMock, service: MultilingualService
    ) -> None:
        """translate_response() populates response_translation on the context."""
        # Setup: process an English query first so we have a context
        request = _make_request("patent query", lang="en")
        context = service.process(request)

        # Now mock translation for the response direction
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "पेटेंट उत्तर"
        mock_gt_cls.return_value = mock_instance

        # Override effective_language to simulate a Hindi user
        context_hi = context.model_copy(update={"effective_language": "hi"})
        updated = service.translate_response("Patent answer.", context_hi)

        assert updated.response_translation is not None
        assert updated.response_translation.was_translated is True
        assert updated.response_translation.target_language == "hi"

    def test_translate_response_en_to_en_no_api_call(
        self, service: MultilingualService
    ) -> None:
        """translate_response to 'en' skips the API."""
        request = _make_request("patent query", lang="en")
        context = service.process(request)
        # effective_language is already 'en'
        updated = service.translate_response("The answer.", context)
        assert updated.response_translation is not None
        assert updated.response_translation.was_translated is False

    def test_translate_response_preserves_other_fields(
        self, service: MultilingualService
    ) -> None:
        """translate_response() must not alter other fields on the context."""
        request = _make_request("some patent query", lang="en")
        context = service.process(request)
        updated = service.translate_response("Answer.", context)

        assert updated.query_id == context.query_id
        assert updated.raw_query == context.raw_query
        assert updated.effective_language == context.effective_language
