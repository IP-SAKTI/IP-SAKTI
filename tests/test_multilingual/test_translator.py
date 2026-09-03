"""
tests/test_multilingual/test_translator.py

Tests for ip_sakti.multilingual.translator.QueryTranslator.

All tests that would make real network calls use unittest.mock.patch to
replace GoogleTranslator.translate with a controlled return value.
This ensures CI can run without internet access and without rate-limiting.

Covers:
- Identity (same-language) skips API call and returns was_translated=False
- translate_to_retrieval_language (hi→en) returns TranslationResult
- translate_response (en→hi) returns TranslationResult
- TranslationError is raised when GoogleTranslator raises an exception
- UnsupportedLanguageError raised for unknown source/target language
- TranslationResult fields are correctly populated
- original_text is preserved in the result
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ip_sakti.multilingual.exceptions import TranslationError, UnsupportedLanguageError
from ip_sakti.multilingual.language_registry import LanguageRegistry
from ip_sakti.multilingual.translator import QueryTranslator
from ip_sakti.models.multilingual import TranslationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry() -> LanguageRegistry:
    """Real registry from config/languages.yaml."""
    return LanguageRegistry()


@pytest.fixture()
def translator(registry: LanguageRegistry) -> QueryTranslator:
    """QueryTranslator backed by the real registry."""
    return QueryTranslator(registry=registry)


# ---------------------------------------------------------------------------
# Identity (no-op) translation
# ---------------------------------------------------------------------------


class TestTranslatorIdentity:
    def test_en_to_en_skips_translation(self, translator: QueryTranslator) -> None:
        """Translating from 'en' to 'en' must skip the API and return was_translated=False."""
        result = translator.translate_to_retrieval_language(
            "patent filing", source_language="en"
        )
        assert isinstance(result, TranslationResult)
        assert result.was_translated is False
        assert result.translated_text == "patent filing"

    def test_en_response_to_en_skips_translation(
        self, translator: QueryTranslator
    ) -> None:
        """translate_response to 'en' skips translation."""
        result = translator.translate_response(
            "This is the answer.", target_language="en"
        )
        assert result.was_translated is False
        assert result.translated_text == "This is the answer."

    def test_identity_preserves_original_text(
        self, translator: QueryTranslator
    ) -> None:
        """original_text must match input even in the identity path."""
        text = "What is the patent procedure?"
        result = translator.translate_to_retrieval_language(text, source_language="en")
        assert result.original_text == text

    def test_identity_source_and_target_set(
        self, translator: QueryTranslator
    ) -> None:
        """source_language and target_language are correctly populated."""
        result = translator.translate_to_retrieval_language(
            "test query", source_language="en"
        )
        assert result.source_language == "en"
        assert result.target_language == "en"


# ---------------------------------------------------------------------------
# Successful translation (mocked API)
# ---------------------------------------------------------------------------


class TestTranslatorMocked:
    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_hi_to_en_translation(
        self, mock_gt_cls: MagicMock, translator: QueryTranslator
    ) -> None:
        """translate_to_retrieval_language('hi') calls the API and returns result."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "patent filing process in India"
        mock_gt_cls.return_value = mock_instance

        hindi_query = "भारत में पेटेंट दाखिल करने की प्रक्रिया"
        result = translator.translate_to_retrieval_language(
            hindi_query, source_language="hi"
        )

        assert isinstance(result, TranslationResult)
        assert result.was_translated is True
        assert result.source_language == "hi"
        assert result.target_language == "en"
        assert result.translated_text == "patent filing process in India"
        assert result.original_text == hindi_query
        mock_instance.translate.assert_called_once_with(hindi_query)

    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_ta_to_en_translation(
        self, mock_gt_cls: MagicMock, translator: QueryTranslator
    ) -> None:
        """translate_to_retrieval_language('ta') calls the API for Tamil."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "patent procedure for Ayurvedic drugs"
        mock_gt_cls.return_value = mock_instance

        tamil_query = "ஆயுர்வேத மருந்துகளுக்கான காப்புரிமை நடைமுறை"
        result = translator.translate_to_retrieval_language(
            tamil_query, source_language="ta"
        )
        assert result.was_translated is True
        assert result.translated_text == "patent procedure for Ayurvedic drugs"

    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_translate_response_en_to_hi(
        self, mock_gt_cls: MagicMock, translator: QueryTranslator
    ) -> None:
        """translate_response('hi') translates English answer to Hindi."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "पेटेंट दाखिल करने की प्रक्रिया निम्नलिखित है"
        mock_gt_cls.return_value = mock_instance

        answer = "The patent filing process is as follows."
        result = translator.translate_response(answer, target_language="hi")

        assert result.was_translated is True
        assert result.source_language == "en"
        assert result.target_language == "hi"
        assert result.original_text == answer
        assert "पेटेंट" in result.translated_text

    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_translate_response_en_to_ta(
        self, mock_gt_cls: MagicMock, translator: QueryTranslator
    ) -> None:
        """translate_response to Tamil is routed correctly."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "காப்புரிமை விண்ணப்ப நடைமுறை"
        mock_gt_cls.return_value = mock_instance

        result = translator.translate_response(
            "The patent application procedure.", target_language="ta"
        )
        assert result.was_translated is True
        assert result.target_language == "ta"


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


class TestTranslatorErrors:
    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_api_exception_raises_translation_error(
        self, mock_gt_cls: MagicMock, translator: QueryTranslator
    ) -> None:
        """An API exception from GoogleTranslator is wrapped as TranslationError."""
        mock_instance = MagicMock()
        mock_instance.translate.side_effect = Exception("Network timeout")
        mock_gt_cls.return_value = mock_instance

        with pytest.raises(TranslationError, match="Network timeout"):
            translator.translate_to_retrieval_language(
                "some query", source_language="hi"
            )

    @patch("ip_sakti.multilingual.translator.GoogleTranslator")
    def test_none_return_raises_translation_error(
        self, mock_gt_cls: MagicMock, translator: QueryTranslator
    ) -> None:
        """None returned by the API raises TranslationError."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = None
        mock_gt_cls.return_value = mock_instance

        with pytest.raises(TranslationError):
            translator.translate_to_retrieval_language(
                "some query", source_language="hi"
            )

    def test_unsupported_source_language_raises(
        self, translator: QueryTranslator
    ) -> None:
        """An unsupported source language raises UnsupportedLanguageError."""
        with pytest.raises(UnsupportedLanguageError, match="zz"):
            translator.translate_to_retrieval_language("hello", source_language="zz")

    def test_unsupported_target_language_raises(
        self, translator: QueryTranslator
    ) -> None:
        """An unsupported target language raises UnsupportedLanguageError."""
        with pytest.raises(UnsupportedLanguageError, match="xx"):
            translator.translate_response("The answer.", target_language="xx")


# ---------------------------------------------------------------------------
# TranslationResult model
# ---------------------------------------------------------------------------


class TestTranslationResultModel:
    def test_result_fields_present(self, translator: QueryTranslator) -> None:
        """TranslationResult has all expected fields."""
        result = translator.translate_to_retrieval_language("test", source_language="en")
        assert hasattr(result, "source_language")
        assert hasattr(result, "target_language")
        assert hasattr(result, "original_text")
        assert hasattr(result, "translated_text")
        assert hasattr(result, "was_translated")

    def test_was_translated_is_bool(self, translator: QueryTranslator) -> None:
        """was_translated is a bool."""
        result = translator.translate_to_retrieval_language("hello", source_language="en")
        assert isinstance(result.was_translated, bool)
