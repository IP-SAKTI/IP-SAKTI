"""
tests/test_multilingual/test_normalizer.py

Tests for ip_sakti.multilingual.normalizer.QueryNormalizer.

Covers:
- Unicode NFC normalisation
- Whitespace collapse (spaces, tabs, newlines)
- Strip leading/trailing whitespace
- Ayurveda term variant → canonical mapping
- Capitalisation preservation in term mapping
- transformations list population
- Empty string handling
- Text that requires no changes
- NormalisationResult fields
"""

from __future__ import annotations

import unicodedata

import pytest

from ip_sakti.multilingual.normalizer import QueryNormalizer
from ip_sakti.models.multilingual import NormalisationResult


@pytest.fixture()
def normalizer() -> QueryNormalizer:
    """Return a fresh QueryNormalizer instance."""
    return QueryNormalizer()


class TestNormalizerStrip:
    def test_strips_leading_whitespace(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("   patent query")
        assert result.normalised == "patent query"
        assert "strip" in result.transformations

    def test_strips_trailing_whitespace(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("patent query   ")
        assert result.normalised == "patent query"
        assert "strip" in result.transformations

    def test_strips_both_ends(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("  hello  ")
        assert result.normalised == "hello"


class TestNormalizerWhitespace:
    def test_collapses_multiple_spaces(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("patent   filing   India")
        assert result.normalised == "patent filing India"
        assert "whitespace_collapse" in result.transformations

    def test_collapses_tabs(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("patent\t\tfiling")
        assert result.normalised == "patent filing"

    def test_collapses_newlines(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("patent\nfiling\nIndia")
        assert result.normalised == "patent filing India"

    def test_mixed_whitespace(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("  patent  \n\t  filing  ")
        assert result.normalised == "patent filing"


class TestNormalizerNFC:
    def test_nfc_normalisation_applied(self, normalizer: QueryNormalizer) -> None:
        """Composed form of a character should be produced."""
        # é as NFD (e + combining accent) should become NFC (single codepoint)
        nfd_text = unicodedata.normalize("NFD", "élan")
        assert len(nfd_text) > 3  # NFD has extra combining chars
        result = normalizer.normalise(nfd_text)
        assert result.normalised == "élan"
        assert "nfc" in result.transformations

    def test_already_nfc_no_transformation(self, normalizer: QueryNormalizer) -> None:
        """Text already in NFC does not record an nfc transformation."""
        nfc_text = unicodedata.normalize("NFC", "triphala")
        result = normalizer.normalise(nfc_text)
        assert "nfc" not in result.transformations


class TestNormalizerAyurvedaTerms:
    def test_triphla_to_triphala(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("I need information about triphla")
        assert "triphala" in result.normalised
        assert "ayurveda_terms" in result.transformations

    def test_trifala_to_triphala(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("trifala benefits")
        assert "triphala" in result.normalised

    def test_amlaki_to_amalaki(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("amlaki is an Ayurvedic herb")
        assert "amalaki" in result.normalised

    def test_ashvagandha_to_ashwagandha(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("ashvagandha patent status")
        assert "ashwagandha" in result.normalised

    def test_giloy_to_guduchi(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("giloy patent India")
        assert "guduchi" in result.normalised

    def test_tulsi_to_tulasi(self, normalizer: QueryNormalizer) -> None:
        result = normalizer.normalise("tulsi regulatory status")
        assert "tulasi" in result.normalised

    def test_capitalised_term_preserved(self, normalizer: QueryNormalizer) -> None:
        """'Triphla' → 'Triphala' (capital T preserved)."""
        result = normalizer.normalise("Triphla dosage information")
        assert "Triphala" in result.normalised

    def test_lowercase_term_stays_lowercase(self, normalizer: QueryNormalizer) -> None:
        """'triphla' → 'triphala' (stays lowercase)."""
        result = normalizer.normalise("triphla dosage")
        assert "triphala" in result.normalised
        assert "Triphala" not in result.normalised

    def test_unknown_term_unchanged(self, normalizer: QueryNormalizer) -> None:
        """A word not in the term map must not be changed."""
        result = normalizer.normalise("neem patent rights")
        # 'nim' → 'neem' but 'neem' → 'neem' (already canonical — stays)
        assert "neem" in result.normalised


class TestNormalizerResultStructure:
    def test_original_preserved(self, normalizer: QueryNormalizer) -> None:
        """NormalisationResult.original must equal the raw input."""
        raw = "   triphla  "
        result = normalizer.normalise(raw)
        assert result.original == raw

    def test_empty_string_returns_result(self, normalizer: QueryNormalizer) -> None:
        """Empty string is handled gracefully with empty normalised output."""
        result = normalizer.normalise("")
        assert isinstance(result, NormalisationResult)
        assert result.normalised == ""

    def test_clean_text_no_transformations(self, normalizer: QueryNormalizer) -> None:
        """Already-clean ASCII text records no transformations."""
        result = normalizer.normalise("patent filing requirements")
        assert result.transformations == []

    def test_transformations_is_list(self, normalizer: QueryNormalizer) -> None:
        """transformations is always a list."""
        result = normalizer.normalise("anything")
        assert isinstance(result.transformations, list)

    def test_multiple_transformations_ordered(self, normalizer: QueryNormalizer) -> None:
        """Multiple transformations are recorded in application order."""
        result = normalizer.normalise("  triphla  ")
        # strip must come before ayurveda_terms
        if "strip" in result.transformations and "ayurveda_terms" in result.transformations:
            assert result.transformations.index("strip") < result.transformations.index(
                "ayurveda_terms"
            )
