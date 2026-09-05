"""
ip_sakti.api.main — FastAPI application server for IP-SAKTI Sahayak.

Provides REST API endpoints for /health, /query, and /document/{source_id}.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from ip_sakti.api.schemas import APIQueryRequest, APIQueryResponse, HealthResponse
from ip_sakti.models.query import FormulationCategory, Jurisdiction, QueryRequest
from ip_sakti.retrieval.sources import SourceRegistry
from ip_sakti.service import IPSAKTIService

logger = logging.getLogger(__name__)

# Singleton service instance
service: IPSAKTIService | None = None


def get_service() -> IPSAKTIService:
    """Return initialised IPSAKTIService instance."""
    global service
    if service is None:
        service = IPSAKTIService()
    return service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler for FastAPI app initialization."""
    logger.info("Initializing IP-SAKTI Sahayak FastAPI application...")
    get_service()
    yield
    logger.info("Shutting down IP-SAKTI Sahayak FastAPI application...")


app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="Multilingual AI-Assisted Decision Support System for Traditional Knowledge & IP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Healthcheck endpoint verifying system readiness."""
    return HealthResponse()


@app.post("/query", response_model=APIQueryResponse, tags=["Query"])
async def process_query(payload: APIQueryRequest) -> APIQueryResponse:
    """
    Process user query through the full core pipeline.

    Accepts raw query text and optional jurisdiction/formulation filters.
    Returns source-grounded response or safe abstention.
    """
    if not payload.raw_query or not payload.raw_query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="raw_query cannot be empty or whitespace.",
        )

    # Parse jurisdiction safely
    j_enum = Jurisdiction.UNKNOWN
    try:
        j_enum = Jurisdiction(payload.jurisdiction.lower())
    except ValueError:
        logger.debug(f"Unrecognised jurisdiction '{payload.jurisdiction}', defaulting to UNKNOWN.")

    # Parse formulation category safely
    f_enum = FormulationCategory.UNKNOWN
    try:
        f_enum = FormulationCategory(payload.formulation_category.lower())
    except ValueError:
        logger.debug(
            f"Unrecognised formulation category '{payload.formulation_category}', defaulting to UNKNOWN."
        )

    query_req = QueryRequest(
        raw_query=payload.raw_query,
        jurisdiction=j_enum,
        formulation_category=f_enum,
        user_language=payload.user_language,
    )

    try:
        srv = get_service()
        final_resp = srv.process_query(query_req)

        agents_str = [a.value for a in final_resp.agents_invoked]

        return APIQueryResponse(
            query_id=final_resp.query_id,
            answer=final_resp.answer,
            is_abstention=final_resp.is_abstention,
            confidence=final_resp.confidence,
            evidence=final_resp.evidence,
            citations=final_resp.citations,
            agents_invoked=agents_str,
            disclaimer=final_resp.disclaimer,
        )
    except Exception as exc:
        logger.error(f"Error processing query in API endpoint: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while processing the query: {exc}",
        )


# ---------------------------------------------------------------------------
# Source document redirect endpoint
# ---------------------------------------------------------------------------

# Singleton SourceRegistry loaded once and reused across requests.
_source_registry = None


def get_source_registry():
    """Return the cached SourceRegistry singleton."""
    global _source_registry
    if _source_registry is None:
        _source_registry = SourceRegistry()
    return _source_registry


@app.get(
    "/document/{source_id}",
    tags=["Documents"],
    summary="Redirect to the canonical source document URL.",
    responses={
        302: {"description": "Redirect to canonical source URL."},
        404: {"description": "Unknown source identifier."},
    },
)
async def get_source_document(source_id: str) -> RedirectResponse:
    """
    Return an HTTP 302 redirect to the canonical URL of the source document
    identified by *source_id*.

    Only source IDs registered in config/sources.json are accepted.
    This endpoint cannot be used to access arbitrary filesystem paths
    or perform path traversal.

    Parameters
    ----------
    source_id :
        The source registry identifier (e.g. 'ayush_rule_158b').

    Returns
    -------
    RedirectResponse
        302 redirect to the canonical source URL.

    Raises
    ------
    HTTPException 404
        If the source_id is not found in the registry.
    """
    registry = get_source_registry()
    source_meta = registry.get_source(source_id)

    if source_meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document '{source_id}' not found in the knowledge registry.",
        )

    canonical_url = source_meta.url
    if not canonical_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No URL available for source '{source_id}'.",
        )

    logger.info(
        "Redirecting to source document",
        extra={"source_id": source_id, "url": canonical_url},
    )
    return RedirectResponse(url=canonical_url, status_code=302)
