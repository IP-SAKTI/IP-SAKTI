"""
ip_sakti.multilingual.normalizer — Query normalisation component.

Applies a sequence of text-cleaning and standardisation steps to the raw
user query before it is passed to the translator and retrieval pipeline.

Normalisation is language-agnostic where possible (Unicode NFC, whitespace
collapse) and applies a small Ayurveda-domain term mapping that corrects
common spelling variants of traditional herb and formulation names.

Approved per AGENTS.md §9: modules must be small and single-purpose.
"""

from __future__ import annotations

import logging
import re
import unicodedata

from ip_sakti.models.multilingual import NormalisationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ayurveda-specific term normalisation map
#
# Maps variant spellings → canonical spelling.
# Keys are lowercase; regex matching is case-insensitive so the canonical
# replacement preserves original capitalisation of the first letter.
#
# Extend this dict as more canonical forms are identified from authoritative
# sources (CCRAS, AYUSH guidelines, etc.).
# ---------------------------------------------------------------------------

_AYURVEDA_TERM_MAP: dict[str, str] = {
    # Triphala
    "triphla": "triphala",
    "trifala": "triphala",
    "tripala": "triphala",
    # Amalaki / Amla
    "amlaki": "amalaki",
    "aamalaki": "amalaki",
    "amla": "amalaki",
    # Ashwagandha
    "ashvagandha": "ashwagandha",
    "aswagandha": "ashwagandha",
    "assvagandha": "ashwagandha",
    # Shatavari
    "satavari": "shatavari",
    "shatawari": "shatavari",
    # Brahmi
    "bramhi": "brahmi",
    # Haritaki
    "haritaki": "haritaki",   # canonical — included to catch diacritics
    "haritky": "haritaki",
    # Bibhitaki
    "vibhitaki": "bibhitaki",
    "behada": "bibhitaki",
    # Guduchi / Giloy
    "giloy": "guduchi",
    "giloi": "guduchi",
    # Neem
    "nim": "neem",
    # Turmeric / Haridra
    "haldi": "haridra",
    "turmeric": "haridra",
    # Tulasi
    "tulsi": "tulasi",
    # Pushkarmool
    "pushkarmul": "pushkarmool",
}

# Pre-compiled patterns: (pattern, canonical_replacement)
# We sort by length descending so longer variants match before shorter ones.
_AYURVEDA_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b" + re.escape(variant) + r"\b", re.IGNORECASE), canonical)
    for variant, canonical in sorted(
        _AYURVEDA_TERM_MAP.items(), key=lambda kv: len(kv[0]), reverse=True
    )
]


class QueryNormalizer:
    """
    Applies deterministic text normalisation to a raw user query.

    Steps (applied in order)
    ------------------------
    1. Strip leading/trailing whitespace.
    2. Unicode NFC normalisation.
    3. Whitespace collapse (multiple spaces/tabs/newlines → single space).
    4. Ayurveda domain term normalisation (variant spellings → canonical).

    Each step that produces a change is recorded in
    ``NormalisationResult.transformations``.
    """

    def normalise(self, text: str) -> NormalisationResult:
        """
        Normalise *text* and return a ``NormalisationResult``.

        Parameters
        ----------
        text :
            The raw query string.  May be empty (returns an empty
            ``NormalisationResult`` without error).

        Returns
        -------
        NormalisationResult
            Contains the original text, normalised text, and the ordered
            list of transformations that changed the text.
        """
        original = text
        current = text
        transformations: list[str] = []

        # Step 1 — Strip
        stripped = current.strip()
        if stripped != current:
            transformations.append("strip")
            current = stripped

        # Step 2 — Unicode NFC
        nfc = unicodedata.normalize("NFC", current)
        if nfc != current:
            transformations.append("nfc")
            current = nfc

        # Step 3 — Whitespace collapse
        collapsed = re.sub(r"[ \t\r\n]+", " ", current).strip()
        if collapsed != current:
            transformations.append("whitespace_collapse")
            current = collapsed

        # Step 4 — Ayurveda term normalisation
        after_ayurveda = self._apply_ayurveda_terms(current)
        if after_ayurveda != current:
            transformations.append("ayurveda_terms")
            current = after_ayurveda

        if transformations:
            logger.debug(
                "Query normalised",
                extra={"transformations": transformations},
            )

        return NormalisationResult(
            original=original,
            normalised=current,
            transformations=transformations,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_ayurveda_terms(text: str) -> str:
        """
        Replace known Ayurveda spelling variants with canonical forms.

        Replacement preserves the original capitalisation of the first
        character of the matched word.
        """
        result = text
        for pattern, canonical in _AYURVEDA_PATTERNS:
            result = pattern.sub(
                lambda m: _match_case(m.group(0), canonical),
                result,
            )
        return result


def _match_case(original_match: str, canonical: str) -> str:
    """
    Return *canonical* with the first character's case matching *original_match*.

    Examples
    --------
    >>> _match_case("Triphla", "triphala")
    'Triphala'
    >>> _match_case("TRIPHLA", "triphala")
    'triphala'   # only first char is checked
    >>> _match_case("triphla", "triphala")
    'triphala'
    """
    if not original_match or not canonical:
        return canonical
    if original_match[0].isupper():
        return canonical[0].upper() + canonical[1:]
    return canonical
