"""
ip_sakti.orchestrator.classifier — Intent, Jurisdiction, and Formulation classifiers.

Classifies incoming user queries using rule-based heuristics and keyword analysis
to determine intent (IP, Regulatory, TK/ABS, Ambiguous), jurisdiction scope
(India, International, Both, Unknown), and Ayurvedic formulation category.
"""

from __future__ import annotations

import logging
import re

from ip_sakti.models.query import FormulationCategory, Intent, Jurisdiction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Keyword lists for heuristic classification
# ---------------------------------------------------------------------------

_IP_KEYWORDS = {
    "patent", "prior art", "prior-art", "cgdptm", "wipo", "patentability",
    "section 3", "section 3(p)", "section 3p", "claim", "novelty", "inventive step",
    "patent office", "pct", "trademark", "copyright", "geographical indication", "gi tag",
}

_REGULATORY_KEYWORDS = {
    "drug", "drugs", "licence", "license", "licensing", "drugs and cosmetics",
    "rule 158", "rule 158b", "rule 158-b", "ayush", "first schedule", "pharmacopoeia",
    "gmp", "good manufacturing", "clinical trial", "safety", "efficacy", "labeling",
    "cosmetic", "nutraceutical", "phytopharmaceutical", "ayurveda-aahar",
}

_TK_ABS_KEYWORDS = {
    "traditional knowledge", "tk", "tkdl", "biodiversity", "abs", "access and benefit sharing",
    "national biodiversity authority", "nba", "sbb", "state biodiversity board",
    "biological resource", "biological diversity act", "ayurvedic text", "heritage",
}

_INDIA_JURISDICTION_KEYWORDS = {
    "india", "indian", "cgdptm", "ayush", "nba", "national biodiversity authority",
    "drugs and cosmetics act", "biological diversity act", "delhi", "mumbai", "chennai", "kolkata",
}

_INTL_JURISDICTION_KEYWORDS = {
    "international", "wipo", "pct", "uspto", "epo", "patent cooperation treaty",
    "united states", "europe", "japan", "foreign", "global",
}


class QueryClassifier:
    """Classifies user query intent, jurisdiction, and formulation category."""

    def classify_intent(self, query_text: str) -> Intent:
        """
        Classify the primary intent of the query text.

        Parameters
        ----------
        query_text :
            Normalised / translated query text.

        Returns
        -------
        Intent
            IP, REGULATORY, TK_ABS, or AMBIGUOUS.
        """
        text_lower = query_text.lower()
        words = set(re.findall(r"\w+", text_lower))

        ip_score = len(words.intersection(_IP_KEYWORDS)) + sum(
            1 for kw in _IP_KEYWORDS if " " in kw and kw in text_lower
        )
        reg_score = len(words.intersection(_REGULATORY_KEYWORDS)) + sum(
            1 for kw in _REGULATORY_KEYWORDS if " " in kw and kw in text_lower
        )
        tk_score = len(words.intersection(_TK_ABS_KEYWORDS)) + sum(
            1 for kw in _TK_ABS_KEYWORDS if " " in kw and kw in text_lower
        )

        scores = {"ip": ip_score, "reg": reg_score, "tk": tk_score}
        max_score = max(scores.values())

        if max_score == 0:
            logger.debug("No intent keywords matched, returning AMBIGUOUS")
            return Intent.AMBIGUOUS

        # Check for tie
        matching_intents = [k for k, v in scores.items() if v == max_score]
        if len(matching_intents) > 1:
            return Intent.AMBIGUOUS

        winner = matching_intents[0]
        if winner == "ip":
            return Intent.IP
        elif winner == "reg":
            return Intent.REGULATORY
        else:
            return Intent.TK_ABS

    def analyze_jurisdiction(
        self,
        query_text: str,
        user_selected: Jurisdiction = Jurisdiction.UNKNOWN,
    ) -> Jurisdiction:
        """
        Resolve applicable jurisdiction.

        User selection takes precedence if provided and non-UNKNOWN.
        Otherwise, query text is analyzed for jurisdiction keywords.

        Parameters
        ----------
        query_text :
            Normalised / translated query text.
        user_selected :
            Jurisdiction explicitly selected by user in UI/API.

        Returns
        -------
        Jurisdiction
            Resolved jurisdiction (INDIA, INTERNATIONAL, BOTH, or UNKNOWN).
        """
        if user_selected != Jurisdiction.UNKNOWN:
            return user_selected

        text_lower = query_text.lower()

        has_india = any(kw in text_lower for kw in _INDIA_JURISDICTION_KEYWORDS)
        has_intl = any(kw in text_lower for kw in _INTL_JURISDICTION_KEYWORDS)

        if has_india and has_intl:
            return Jurisdiction.BOTH
        elif has_india:
            return Jurisdiction.INDIA
        elif has_intl:
            return Jurisdiction.INTERNATIONAL
        else:
            return Jurisdiction.UNKNOWN

    def classify_formulation(
        self,
        query_text: str,
        user_selected: FormulationCategory = FormulationCategory.UNKNOWN,
    ) -> FormulationCategory:
        """
        Identify formulation/product category.

        User selection takes precedence if provided and non-UNKNOWN.

        Parameters
        ----------
        query_text :
            Normalised / translated query text.
        user_selected :
            Formulation category selected by user.

        Returns
        -------
        FormulationCategory
            Resolved formulation category.
        """
        if user_selected != FormulationCategory.UNKNOWN:
            return user_selected

        text_lower = query_text.lower()

        if "cosmetic" in text_lower:
            return FormulationCategory.COSMETIC
        elif "nutraceutical" in text_lower or "ayurveda-aahar" in text_lower or "food" in text_lower:
            return FormulationCategory.NUTRACEUTICAL
        elif "phytopharmaceutical" in text_lower:
            return FormulationCategory.PHYTOPHARMACEUTICAL
        elif "new drug" in text_lower or "non-classical" in text_lower:
            return FormulationCategory.NEW_DRUG
        elif "proprietary" in text_lower or "patent drug" in text_lower:
            return FormulationCategory.PROPRIETARY
        elif "classical" in text_lower or "generic" in text_lower or "samhita" in text_lower or "first schedule" in text_lower:
            return FormulationCategory.CLASSICAL
        else:
            return FormulationCategory.UNKNOWN
