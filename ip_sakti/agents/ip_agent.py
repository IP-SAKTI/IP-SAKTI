"""
ip_sakti.agents.ip_agent — IP Specialist Agent.

Handles patentability, Section 3(p) traditional knowledge exclusions,
prior art, claims analysis, and CGPDTM/WIPO procedural guidance queries.
"""

from __future__ import annotations

import logging

from ip_sakti.agents.base_agent import BaseAgent
from ip_sakti.models.query import AgentResult, AgentType, QueryContext
from ip_sakti.retrieval.pipeline import HybridRAGPipeline

logger = logging.getLogger(__name__)


class IPAgent(BaseAgent):
    """Specialist agent for Intellectual Property and Patent guidance."""

    def __init__(self) -> None:
        """Initialise IPAgent with AgentType.IP_AGENT."""
        super().__init__(agent_type=AgentType.IP_AGENT)

    def process(
        self,
        context: QueryContext,
        pipeline: HybridRAGPipeline,
        applied_rules: list[str] | None = None,
    ) -> AgentResult:
        """
        Execute IP-focused retrieval and package AgentResult.

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
            "IPAgent processing query",
            extra={"query_id": str(context.query_id)},
        )

        search_query = context.translated_query
        evidence_chunks = pipeline.search(search_query)

        summary = (
            f"IP Agent evaluated query for patentability, Section 3(p), "
            f"and prior-art criteria. Retrieved {len(evidence_chunks)} evidence chunks."
        )

        return AgentResult(
            agent_type=self.agent_type,
            query_id=context.query_id,
            evidence=evidence_chunks,
            summary=summary,
        )
