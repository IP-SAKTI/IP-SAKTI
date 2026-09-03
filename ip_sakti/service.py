"""
ip_sakti.service — High-level application service & SQLite query persistence wrapper.

Provides the primary application entry point (IPSAKTIService) for query handling
and records query execution metrics, classification metadata, and responses
into the SQLite database.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from ip_sakti.llm import AnswerSynthesisService, SafeAbstentionHandler
from ip_sakti.models.query import FinalResponse, QueryRequest
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.utils.db import DatabaseManager

logger = logging.getLogger(__name__)


class IPSAKTIService:
    """
    High-level application service wrapper for IP-SAKTI Sahayak.

    Coordinates query processing via PipelineCoordinator and handles SQLite DB persistence.
    """

    def __init__(
        self,
        coordinator: PipelineCoordinator | None = None,
        db_manager: DatabaseManager | None = None,
    ) -> None:
        """Initialise service with optional coordinator and database manager."""
        self.db = db_manager or DatabaseManager()
        self.db.initialise()

        if coordinator is not None:
            self.coordinator = coordinator
        else:
            abstention_hnd = SafeAbstentionHandler(db_manager=self.db)
            synthesis = AnswerSynthesisService(abstention_handler=abstention_hnd)
            self.coordinator = PipelineCoordinator(synthesis_service=synthesis)
        logger.debug("IPSAKTIService initialised")

    def process_query(self, request: QueryRequest) -> FinalResponse:
        """
        Process a QueryRequest through the pipeline and log to SQLite database.

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

        # Pre-insert parent query record to satisfy foreign key constraint on escalations
        try:
            conn = self.db.connection
            with conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO queries (
                        query_id, raw_query, detected_lang, jurisdiction,
                        formulation_cat, is_abstention, created_at
                    ) VALUES (?, ?, ?, ?, ?, 0, ?)
                    """,
                    (
                        str(request.query_id),
                        request.raw_query,
                        request.user_language,
                        request.jurisdiction.value,
                        request.formulation_category.value,
                        now_iso,
                    ),
                )
        except Exception as exc:
            logger.error(f"Failed to pre-log query record to database: {exc}")

        # Execute full pipeline
        response = self.coordinator.execute(request)

        # Update query record with final execution metrics and agents
        try:
            agents_json = json.dumps([a.value for a in response.agents_invoked]) if response.agents_invoked else "[]"
            confidence_score = response.confidence.score if response.confidence else None

            conn = self.db.connection
            with conn:
                conn.execute(
                    """
                    UPDATE queries SET
                        agents_invoked = ?,
                        is_abstention = ?,
                        confidence_score = ?
                    WHERE query_id = ?
                    """,
                    (
                        agents_json,
                        1 if response.is_abstention else 0,
                        confidence_score,
                        str(request.query_id),
                    ),
                )
            logger.debug(
                "Logged query record to database",
                extra={"query_id": str(request.query_id)},
            )
        except Exception as exc:
            logger.error(f"Failed to log query record to database: {exc}")

        return response
