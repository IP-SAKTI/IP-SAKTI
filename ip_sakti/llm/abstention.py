"""
ip_sakti.llm.abstention — Safe abstention and human/IP facilitator escalation handler.

Approved per AGENTS.md §7: Implement safe abstention — if confidence is below threshold
or evidence is insufficient, the system must decline to answer and escalate to the human/IP facilitator pathway.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from ip_sakti.models.query import AgentType, EscalationRecord, FinalResponse
from ip_sakti.utils.db import DatabaseManager

logger = logging.getLogger(__name__)

_ABSTENTION_TEXT = (
    "I cannot provide a definitive or source-grounded answer to your query because the available "
    "authoritative knowledge base evidence is insufficient or uncertain for this topic. "
    "To ensure legal and regulatory safety, this query has been logged and escalated to the "
    "Human / IP Facilitator pathway for professional review."
)


class SafeAbstentionHandler:
    """Handles safe abstention generation and database escalation logging."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        """Initialise abstention handler with database manager."""
        self._db = db_manager or DatabaseManager()

    def handle_abstention(
        self,
        query_id: UUID,
        reason: str,
        agent_type: Optional[AgentType] = None,
    ) -> FinalResponse:
        """
        Create a safe abstention response and log escalation record to SQLite DB.

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

        try:
            conn = self._db.connection
            now_iso = datetime.now(timezone.utc).isoformat()
            with conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO queries (
                        query_id, raw_query, is_abstention, created_at
                    ) VALUES (?, 'Escalated query', 1, ?)
                    """,
                    (str(record.query_id), now_iso),
                )
                conn.execute(
                    """
                    INSERT INTO escalations (
                        query_id, agent_type, reason, escalated_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(record.query_id),
                        record.agent_type.value if record.agent_type else None,
                        record.reason,
                        now_iso,
                    ),
                )
            logger.info(
                "Logged escalation record to database",
                extra={"query_id": str(query_id), "reason": reason},
            )
        except Exception as exc:
            logger.error(f"Failed to record escalation in database: {exc}")

        return FinalResponse(
            query_id=query_id,
            answer=_ABSTENTION_TEXT,
            is_abstention=True,
        )
