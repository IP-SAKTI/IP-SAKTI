"""
ip_sakti.agents.regulatory_agent — Regulatory Specialist Agent.

Handles Drugs & Cosmetics Act/Rules, Rule 158-B, Ministry of AYUSH licensing,
and classical vs. proprietary drug proof requirement queries.
"""

from __future__ import annotations

import logging

from ip_sakti.agents.base_agent import BaseAgent
from ip_sakti.models.query import AgentResult, AgentType, QueryContext
from ip_sakti.retrieval.pipeline import HybridRAGPipeline

logger = logging.getLogger(__name__)


class RegulatoryAgent(BaseAgent):
    """Specialist agent for Regulatory compliance and licensing guidance."""

    def __init__(self) -> None:
        """Initialise RegulatoryAgent with AgentType.REGULATORY_AGENT."""
        super().__init__(agent_type=AgentType.REGULATORY_AGENT)

    def process(
        self,
        context: QueryContext,
        pipeline: HybridRAGPipeline,
        applied_rules: list[str] | None = None,
    ) -> AgentResult:
        """
        Execute regulatory-focused retrieval and package AgentResult.

        Parameters
        ----------
        context :
            Enriched QueryContext model.
        pipeline :
            Stage 3 HybridRAGPipeline instance.
        applied_rules :
            Domain guidance strings from RuleEngine.

        Returns
        -------
        AgentResult
            Retrieved evidence chunks and agent execution summary.
        """
        logger.info(
            "RegulatoryAgent processing query",
            extra={"query_id": str(context.query_id)},
        )

        search_query = context.translated_query
        evidence_chunks = pipeline.search(search_query)

        summary = (
            f"Regulatory Agent evaluated query for Drugs & Cosmetics Rules, "
            f"Rule 158-B, and AYUSH licensing. Retrieved {len(evidence_chunks)} evidence chunks."
        )

        return AgentResult(
            agent_type=self.agent_type,
            query_id=context.query_id,
            evidence=evidence_chunks,
            summary=summary,
        )
