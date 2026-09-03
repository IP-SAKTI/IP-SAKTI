"""
ip_sakti.agents.base_agent — Abstract base class for specialist agents.

Defines the core interface and shared RAG retrieval integration for all
three specialist agents: IPAgent, RegulatoryAgent, and TKABSAgent.

Approved per AGENTS.md §3: There are exactly three specialist agents.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from ip_sakti.models.query import AgentResult, AgentType, QueryContext
from ip_sakti.retrieval.pipeline import HybridRAGPipeline

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract Base Class for specialist agents in IP-SAKTI Sahayak.

    Attributes
    ----------
    agent_type :
        AgentType identifier (IP_AGENT, REGULATORY_AGENT, TK_ABS_AGENT).
    """

    def __init__(self, agent_type: AgentType) -> None:
        """Initialise base agent with agent type."""
        self.agent_type = agent_type

    @abstractmethod
    def process(
        self,
        context: QueryContext,
        pipeline: HybridRAGPipeline,
        applied_rules: list[str] | None = None,
    ) -> AgentResult:
        """
        Process query context, execute domain retrieval, and return AgentResult.

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
            Structured result containing retrieved evidence chunks and reasoning metadata.
        """
