"""
ip_sakti.agents.tk_abs_agent — TK/ABS Specialist Agent.

Handles Traditional Knowledge, Biological Diversity Act 2002, Access and Benefit
Sharing (ABS), National Biodiversity Authority (NBA) approvals, and State Biodiversity
Board (SBB) queries.
"""

from __future__ import annotations

import logging

from ip_sakti.agents.base_agent import BaseAgent
from ip_sakti.models.query import AgentResult, AgentType, QueryContext
from ip_sakti.retrieval.pipeline import HybridRAGPipeline

logger = logging.getLogger(__name__)


class TKABSAgent(BaseAgent):
    """Specialist agent for Traditional Knowledge and Access & Benefit Sharing guidance."""

    def __init__(self) -> None:
        """Initialise TKABSAgent with AgentType.TK_ABS_AGENT."""
        super().__init__(agent_type=AgentType.TK_ABS_AGENT)

    def process(
        self,
        context: QueryContext,
        pipeline: HybridRAGPipeline,
        applied_rules: list[str] | None = None,
    ) -> AgentResult:
        """
        Execute TK/ABS-focused retrieval and package AgentResult.

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
            "TKABSAgent processing query",
            extra={"query_id": str(context.query_id)},
        )

        search_query = context.translated_query
        tk_keywords = ["traditional knowledge", "tk", "tkdl", "biodiversity", "abs", "nba", "sbb", "biological resource"]
        if search_query and not any(kw in search_query.lower() for kw in tk_keywords):
            search_query = f"{search_query} Traditional Knowledge Biological Diversity Act Access and Benefit Sharing NBA"

        evidence_chunks = pipeline.search(search_query)

        summary = (
            f"TK/ABS Agent evaluated query for Biological Diversity Act 2002, "
            f"Access and Benefit Sharing, and NBA approvals. Retrieved {len(evidence_chunks)} evidence chunks."
        )

        return AgentResult(
            agent_type=self.agent_type,
            query_id=context.query_id,
            evidence=evidence_chunks,
            summary=summary,
        )
