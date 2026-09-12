"""
ip_sakti.service — High-level application service & Supabase query persistence wrapper.

Provides the primary application entry point (IPSAKTIService) for query handling
and records query execution metrics, classification metadata, and responses
into Supabase PostgreSQL.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from ip_sakti.llm import AnswerSynthesisService, SafeAbstentionHandler
from ip_sakti.models.query import FinalResponse, QueryRequest
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class IPSAKTIService:
    """
    High-level application service wrapper for IP-SAKTI Sahayak.

    Coordinates query processing via PipelineCoordinator and handles Supabase DB persistence.
    """

    def __init__(
        self,
        coordinator: PipelineCoordinator | None = None,
        db_manager: Any = None,
    ) -> None:
        """Initialise service with optional coordinator."""
        self.db = db_manager
        self.db_manager = db_manager
        self.supabase_client = SupabaseClient()

        if coordinator is not None:
            self.coordinator = coordinator
        else:
            abstention_hnd = SafeAbstentionHandler(db_manager=db_manager)
            synthesis = AnswerSynthesisService(abstention_handler=abstention_hnd)
            self.coordinator = PipelineCoordinator(synthesis_service=synthesis)
        logger.debug("IPSAKTIService initialised")

    def process_query(self, request: QueryRequest) -> FinalResponse:
        """
        Process a QueryRequest through the pipeline and log to Supabase PostgreSQL.

        Parameters
        ----------
        request :
            Incoming QueryRequest instance.

        Returns
        -------
        FinalResponse
            Final response object containing answer or safe abstention.
        """
        logger.info(
            "Processing query via IPSAKTIService",
            extra={"query_id": str(request.query_id)},
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        if self.db:
            try:
                conn = self.db.connection
                with conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO queries (query_id, raw_query, detected_lang, is_abstention, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (str(request.query_id), request.raw_query, request.user_language, 0, now_iso),
                    )
            except Exception as exc:
                logger.debug(f"Local SQLite query log failed: {exc}")

        # Log query metadata to Supabase if configured (optional telemetry)
        if self.supabase_client.is_configured:
            try:
                self.supabase_client.insert(
                    table="queries",
                    data={
                        "query_id": str(request.query_id),
                        "user_id": request.user_id,
                        "raw_query": request.raw_query,
                        "detected_lang": request.user_language,
                        "jurisdiction": request.jurisdiction.value if request.jurisdiction else None,
                        "formulation_cat": request.formulation_category.value if request.formulation_category else None,
                        "is_abstention": False,
                        "created_at": now_iso,
                    },
                    use_service_role=True if self.supabase_client.service_role_key else False,
                )
            except Exception as exc:
                if "PGRST205" in str(exc) or "404" in str(exc):
                    logger.debug(f"Telemetry table 'queries' not present in Supabase schema: {exc}")
                else:
                    logger.warning(f"Failed to log query record to Supabase: {exc}")

        # Execute full pipeline
        response = self.coordinator.execute(request)

        if response.is_abstention and self.db:
            try:
                conn = self.db.connection
                with conn:
                    conn.execute(
                        """
                        INSERT INTO escalations (query_id, agent_type, reason, escalated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            str(request.query_id),
                            "general",
                            response.abstention_reason or "Low confidence / zero evidence safe abstention",
                            now_iso,
                        ),
                    )
            except Exception as exc:
                logger.debug(f"Local SQLite escalation log failed: {exc}")

        if self.supabase_client.is_configured:
            try:
                agents_list = [a.value for a in response.agents_invoked] if response.agents_invoked else []
                confidence_score = response.confidence.score if response.confidence else None

                self.supabase_client.update(
                    table="queries",
                    data={
                        "agents_invoked": agents_list,
                        "is_abstention": response.is_abstention,
                        "confidence_score": confidence_score,
                    },
                    params={"query_id": f"eq.{request.query_id}"},
                    use_service_role=True if self.supabase_client.service_role_key else False,
                )
            except Exception as exc:
                if "PGRST205" in str(exc) or "404" in str(exc):
                    logger.debug(f"Telemetry table 'queries' not present in Supabase schema: {exc}")
                else:
                    logger.warning(f"Failed to update query record metrics in Supabase: {exc}")

        return response

