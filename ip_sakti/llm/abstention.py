"""
ip_sakti.llm.abstention — Safe abstention and human/IP facilitator escalation handler.

Approved per AGENTS.md §7: Implement safe abstention — if confidence is below threshold
or evidence is insufficient, the system must decline to answer and escalate to the human/IP facilitator pathway.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from ip_sakti.models.query import AgentType, EscalationRecord, FinalResponse
from ip_sakti.utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

_ABSTENTION_TEXT = (
    "I cannot provide a definitive or source-grounded answer to your query because the available "
    "authoritative knowledge base evidence is insufficient or uncertain for this topic. "
    "To ensure legal and regulatory safety, this query has been logged and escalated to the "
    "Human / IP Facilitator pathway for professional review."
)


class SafeAbstentionHandler:
    """Handles safe abstention generation and database escalation logging."""

    def __init__(self, db_manager: Any = None) -> None:
        """Initialise abstention handler with Supabase client."""
        self.supabase_client = SupabaseClient()

    def handle_abstention(
        self,
        query_id: UUID,
        reason: str,
        agent_type: Optional[AgentType] = None,
    ) -> FinalResponse:
        """
        Create a safe abstention response and log escalation record to Supabase PostgreSQL.

        Parameters
        ----------
        query_id :
            Target query UUID.
        reason :
            Reason for abstention/escalation.
        agent_type :
            Optional specialist agent triggering escalation.

        Returns
        -------
        FinalResponse
            Response object marked with is_abstention=True.
        """
        record = EscalationRecord(
            query_id=query_id,
            reason=reason,
            agent_type=agent_type,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        if self.supabase_client.is_configured:
            try:
                self.supabase_client.insert(
                    table="escalations",
                    data={
                        "query_id": str(record.query_id),
                        "agent_type": record.agent_type.value if record.agent_type else None,
                        "reason": record.reason,
                        "escalated_at": now_iso,
                    },
                    use_service_role=True if self.supabase_client.service_role_key else False,
                )
                logger.info(
                    "Logged escalation record to Supabase",
                    extra={"query_id": str(query_id), "reason": reason},
                )
            except Exception as exc:
                if "PGRST205" in str(exc) or "404" in str(exc):
                    logger.debug(f"Telemetry table 'escalations' not present in Supabase schema: {exc}")
                else:
                    logger.warning(f"Failed to record escalation in Supabase: {exc}")

        return FinalResponse(
            query_id=query_id,
            answer=_ABSTENTION_TEXT,
            is_abstention=True,
        )

