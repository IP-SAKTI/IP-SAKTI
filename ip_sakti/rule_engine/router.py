"""
ip_sakti.rule_engine.router — Agent router component.

Routes QueryContext to appropriate specialist agent(s) (IPAgent, RegulatoryAgent, TKABSAgent).

Approved per AGENTS.md §3: Exactly three specialist agents, exactly one Agent Router.
"""

from __future__ import annotations

import logging

from ip_sakti.models.query import AgentType, Intent, QueryContext

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes QueryContext to target specialist agent(s)."""

    def route(self, context: QueryContext) -> list[AgentType]:
        """
        Determine target agent(s) for a given QueryContext.

        Parameters
        ----------
        context :
            Enriched QueryContext model.

        Returns
        -------
        list[AgentType]
            List of target AgentType enums.
        """
        if context.intent == Intent.IP:
            target_agents = [AgentType.IP_AGENT]
        elif context.intent == Intent.REGULATORY:
            target_agents = [AgentType.REGULATORY_AGENT]
        elif context.intent == Intent.TK_ABS:
            target_agents = [AgentType.TK_ABS_AGENT]
        else:
            # Ambiguous intent: default to routing to IP and Regulatory agents
            logger.info("Ambiguous intent detected; routing to IP and Regulatory agents.")
            target_agents = [AgentType.IP_AGENT, AgentType.REGULATORY_AGENT]

        logger.debug(
            "Query routed to agent(s)",
            extra={"intent": context.intent.value, "agents": [a.value for a in target_agents]},
        )
        return target_agents
