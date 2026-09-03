"""
ip_sakti.orchestrator.orchestrator — Orchestrator component.

Assembles the enriched QueryContext model from QueryRequest and MultilingualContext
by running intent classification, jurisdiction analysis, and formulation classification.
"""

from __future__ import annotations

import logging

from ip_sakti.models.multilingual import MultilingualContext
from ip_sakti.models.query import QueryContext, QueryRequest
from ip_sakti.orchestrator.classifier import QueryClassifier

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main Orchestrator component.

    Consumes QueryRequest and MultilingualContext and produces QueryContext.
    """

    def __init__(self, classifier: QueryClassifier | None = None) -> None:
        """Initialise Orchestrator with optional classifier injection."""
        self.classifier = classifier or QueryClassifier()
        logger.debug("Orchestrator initialised")

    def process(
        self,
        request: QueryRequest,
        multilingual_ctx: MultilingualContext,
    ) -> QueryContext:
        """
        Build and return QueryContext for downstream rule engine and agent routing.

        Parameters
        ----------
        request :
            Incoming user query request.
        multilingual_ctx :
            Processed multilingual context from Stage 2.

        Returns
        -------
        QueryContext
            Enriched query context model.
        """
        query_text = multilingual_ctx.query_translation.translated_text

        intent = self.classifier.classify_intent(query_text)
        jurisdiction = self.classifier.analyze_jurisdiction(
            query_text, user_selected=request.jurisdiction
        )
        formulation = self.classifier.classify_formulation(
            query_text, user_selected=request.formulation_category
        )

        ctx = QueryContext(
            query_id=request.query_id,
            raw_query=request.raw_query,
            normalised_query=multilingual_ctx.normalisation.normalised,
            detected_language=multilingual_ctx.detection.language,
            lang_detect_confidence=multilingual_ctx.detection.confidence,
            translated_query=query_text,
            intent=intent,
            jurisdiction=jurisdiction,
            formulation_category=formulation,
        )

        logger.info(
            "Orchestrator context created",
            extra={
                "query_id": str(request.query_id),
                "intent": intent.value,
                "jurisdiction": jurisdiction.value,
                "formulation_category": formulation.value,
            },
        )
        return ctx
