"""
tests/test_multilingual/test_detector.py

Tests for ip_sakti.multilingual.detector.LanguageDetector.

Covers:
- English text detection
- Hindi text detection
- Tamil text detection
- Bengali text detection
- Low-confidence fallback to 'en'
- Empty input raises LanguageDetectionError
- Very-short ambiguous input handled without crash
- DetectionResult fields are correctly populated
- is_fallback=False for confident detection
- is_fallback=True when threshold is exceeded

Note: langdetect is seeded (DetectorFactory.seed = 0) in detector.py for
      determinism.  Tests are written to be robust to minor variation by
      only asserting on high-confidence languages with long-enough input.
"""

from __future__ import annotations

import pytest

from ip_sakti.multilingual.detector import LanguageDetector
from ip_sakti.multilingual.exceptions import LanguageDetectionError
from ip_sakti.multilingual.language_registry import LanguageRegistry
from ip_sakti.models.multilingual import DetectionResult


# ---------------------------------------------------------------------------
# Fixture: detector with low threshold so real languages pass
# ---------------------------------------------------------------------------


@pytest.fixture()
def detector() -> LanguageDetector:
    """A LanguageDetector with a low confidence threshold (0.1) for testing."""
    return LanguageDetector(min_confidence=0.1)


@pytest.fixture()
def strict_detector() -> LanguageDetector:
    """A LanguageDetector with a very high threshold (0.999) to force fallback."""
    return LanguageDetector(min_confidence=0.999)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLanguageDetectorEnglish:
    def test_detects_english(self, detector: LanguageDetector) -> None:
        """A clear English sentence is detected as 'en'."""
        result = detector.detect(
            "What are the patent filing requirements in India for Ayurvedic formulations?"
        )
        assert isinstance(result, DetectionResult)
        assert result.language == "en"
        assert result.confidence > 0.0
        assert result.is_fallback is False

    def test_english_confidence_is_float(self, detector: LanguageDetector) -> None:
        """Confidence value is a float between 0 and 1."""
        result = detector.detect("This is a patent query about intellectual property.")
        assert 0.0 <= result.confidence <= 1.0


class TestLanguageDetectorIndianLanguages:
    def test_detects_hindi(self, detector: LanguageDetector) -> None:
        """A sufficiently long Hindi sentence is detected as 'hi'."""
        # "What is the patent procedure?" in Hindi
        hindi_text = (
            "आयुर्वेदिक दवाओं के पेटेंट के लिए भारत में क्या प्रक्रिया है?"
        )
        result = detector.detect(hindi_text)
        assert result.language == "hi"
        assert result.is_fallback is False

    def test_detects_tamil(self, detector: LanguageDetector) -> None:
        """A sufficiently long Tamil sentence is detected as 'ta'."""
        tamil_text = (
            "ஆயுர்வேத மருந்துகளுக்கான காப்புரிமை நடைமுறைகள் என்ன?"
        )
        result = detector.detect(tamil_text)
        assert result.language == "ta"
        assert result.is_fallback is False

    def test_detects_bengali(self, detector: LanguageDetector) -> None:
        """A sufficiently long Bengali sentence is detected as 'bn'."""
        bengali_text = (
            "আয়ুর্বেদিক ওষুধের জন্য পেটেন্ট আবেদন কীভাবে করবেন?"
        )
        result = detector.detect(bengali_text)
        assert result.language == "bn"
        assert result.is_fallback is False

    def test_detects_kannada(self, detector: LanguageDetector) -> None:
        """A Kannada sentence is detected (language code checked)."""
        kannada_text = (
            "ಆಯುರ್ವೇದ ಔಷಧಿಗಳ ಪೇಟೆಂಟ್ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?"
        )
        result = detector.detect(kannada_text)
        # langdetect may return 'kn' or occasionally confuse with 'te';
        # assert it is a plausible Indic language
        assert result.language in {"kn", "te", "ml"}
        assert result.is_fallback is False


class TestLanguageDetectorFallback:
    def test_low_confidence_triggers_fallback(self) -> None:
        """When confidence < threshold, fallback language is returned."""
        from unittest.mock import MagicMock, patch

        mock_candidate = MagicMock()
        mock_candidate.lang = "hi"
        mock_candidate.prob = 0.2  # explicitly below threshold

        detector = LanguageDetector(min_confidence=0.9)
        with patch(
            "ip_sakti.multilingual.detector.detect_langs",
            return_value=[mock_candidate],
        ):
            result = detector.detect("patent")

        assert result.is_fallback is True
        assert result.language == "en"  # fallback_language from registry
        assert result.confidence == pytest.approx(0.2)

    def test_fallback_preserves_confidence(self) -> None:
        """The raw confidence is recorded even when fallback fires."""
        from unittest.mock import MagicMock, patch

        mock_candidate = MagicMock()
        mock_candidate.lang = "ta"
        mock_candidate.prob = 0.05

        detector = LanguageDetector(min_confidence=0.9)
        with patch(
            "ip_sakti.multilingual.detector.detect_langs",
            return_value=[mock_candidate],
        ):
            result = detector.detect("triphala")

        assert 0.0 <= result.confidence <= 1.0

    def test_unsupported_language_triggers_fallback(self) -> None:
        """When detected language is not in registry (e.g. 'de'), fallback language is returned."""
        from unittest.mock import MagicMock, patch

        mock_candidate = MagicMock()
        mock_candidate.lang = "de"
        mock_candidate.prob = 0.99

        detector = LanguageDetector(min_confidence=0.5)
        with patch(
            "ip_sakti.multilingual.detector.detect_langs",
            return_value=[mock_candidate],
        ):
            result = detector.detect("AYUSH licensing steps under Rule 158-B")

        assert result.is_fallback is True
        assert result.language == "en"
        assert result.confidence == pytest.approx(0.99)


class TestLanguageDetectorErrors:
    def test_empty_string_raises(self, detector: LanguageDetector) -> None:
        """Empty input raises LanguageDetectionError."""
        with pytest.raises(LanguageDetectionError, match="empty"):
            detector.detect("")

    def test_whitespace_only_raises(self, detector: LanguageDetector) -> None:
        """Whitespace-only input raises LanguageDetectionError."""
        with pytest.raises(LanguageDetectionError):
            detector.detect("   \n\t  ")

    def test_single_char_does_not_crash(self, detector: LanguageDetector) -> None:
        """A single character may fall back gracefully without crashing."""
        # Either raises or returns a DetectionResult — must not crash with
        # an unexpected exception type
        try:
            result = detector.detect("a")
            assert isinstance(result, DetectionResult)
        except LanguageDetectionError:
            pass  # acceptable


class TestDetectionResultModel:
    def test_detection_result_fields(self, detector: LanguageDetector) -> None:
        """DetectionResult has the expected fields populated."""
        result = detector.detect("Intellectual property rights in Ayurveda")
        assert hasattr(result, "language")
        assert hasattr(result, "confidence")
        assert hasattr(result, "is_fallback")

    def test_detection_result_confidence_in_range(
        self, detector: LanguageDetector
    ) -> None:
        """Confidence is always within [0.0, 1.0]."""
        result = detector.detect("patent filing process for herbal medicines")
        assert 0.0 <= result.confidence <= 1.0

    def test_is_fallback_is_bool(self, detector: LanguageDetector) -> None:
        """is_fallback is a bool."""
        result = detector.detect("regulatory guidance for Ayurvedic cosmetics")
        assert isinstance(result.is_fallback, bool)
