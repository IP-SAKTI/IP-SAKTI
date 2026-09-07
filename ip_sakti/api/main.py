"""
ip_sakti.api.main — FastAPI application server for IP-SAKTI Sahayak.

Provides REST API endpoints for /health, /query, and /document/{source_id}.
"""

import html
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from ip_sakti.api.schemas import APIQueryRequest, APIQueryResponse, HealthResponse
from ip_sakti.models.query import FormulationCategory, Jurisdiction, QueryRequest, SourceViewerResponse
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

        logger.info(
            f"[IP-SAKTI RUNTIME answerability-fix-v2] Query: {query_req.raw_query!r} | "
            f"IsAbstention: {final_resp.is_abstention} | EvidenceCount: {len(final_resp.evidence)}"
        )

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


def get_source_registry() -> SourceRegistry:
    """Return the cached SourceRegistry singleton."""
    global _source_registry
    if _source_registry is None:
        _source_registry = SourceRegistry()
    return _source_registry


@app.get(
    "/document/{source_id}",
    tags=["Documents"],
    summary="View or download local source document.",
    responses={
        200: {"description": "Local source document (PDF file or HTML/JSON viewer)."},
        404: {"description": "Unknown source identifier."},
    },
)
async def get_source_document(
    source_id: str,
    format: Optional[str] = Query(default=None, description="Output format: 'pdf', 'html', or 'json'")
) -> Response:
    """
    Serve the IP-SAKTI local source document for the given source_id.

    Prioritises serving the local PDF document via FileResponse (HTTP 200).
    Falls back to the local HTML/JSON source viewer if no PDF exists.
    """
    registry = get_source_registry()

    # Security check 1: Validate source_id against SourceRegistry
    resolved_id = registry.resolve_source_id(source_id)
    if resolved_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document '{source_id}' not found in the knowledge registry.",
        )

    # 1. format = "json" requested
    if format == "json":
        viewer_data = registry.get_source_viewer_data(source_id)
        if viewer_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source document '{source_id}' not found in registry.",
            )
        return JSONResponse(content=viewer_data)

    # 2. Check for local PDF document in data/documents/ (unless format="html" explicitly requested)
    if format != "html":
        local_pdf = registry.get_local_document_file(source_id)
        if local_pdf and local_pdf.is_file():
            logger.info("Serving local PDF document", extra={"source_id": resolved_id, "path": str(local_pdf)})
            return FileResponse(
                path=local_pdf,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'inline; filename="{resolved_id}.pdf"',
                    "X-Content-Type-Options": "nosniff",
                },
            )

    # 3. Fallback to HTML Local Source Viewer page
    viewer_data = registry.get_source_viewer_data(source_id)
    if viewer_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document '{source_id}' not found in the knowledge registry.",
        )

    # Render clean HTML page for the Local Source Document Viewer
    title = html.escape(viewer_data["title"])
    authority = html.escape(viewer_data["authority"])
    doc_type = html.escape(viewer_data["document_type"]).upper()
    jurisdiction = html.escape(viewer_data["jurisdiction"]).upper()
    canonical_sid = html.escape(viewer_data["source_id"])
    official_url = html.escape(viewer_data["official_url"])
    is_auth_url = viewer_data["is_authorised_url"]
    local_available = viewer_data["local_available"]
    content_text = html.escape(viewer_data["content"])

    if local_available and content_text:
        content_html = f"""
        <div class="content-box">
            <h3 class="section-heading">Local Knowledge Base Content</h3>
            <p class="content-body">{content_text}</p>
        </div>
        """
    else:
        content_html = """
        <div class="content-box warning-box">
            <p class="content-warning">Local source document content is not available for this record. You can still access the official external source below.</p>
        </div>
        """

    archive_url = viewer_data.get("archive_url")
    is_valid_archive = viewer_data.get("is_valid_archive_url")

    official_link_html = (
        f'<a href="{official_url}" target="_blank" rel="noopener noreferrer" class="btn-official">🌐 Open Official External Source ↗</a>'
        if is_auth_url
        else '<span class="text-unauthorised">⚠️ Official URL is unverified or unauthorised</span>'
    )

    archive_link_html = (
        f'<a href="{html.escape(archive_url)}" target="_blank" rel="noopener noreferrer" class="btn-archive">🏛️ View Archived Source (Wayback Machine) ↗</a>'
        if is_valid_archive and archive_url
        else ""
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — IP-SAKTI Source Viewer</title>
    <style>
        :root {{
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #0f172a;
            --muted: #64748b;
            --primary: #1e3a8a;
            --primary-hover: #1d4ed8;
            --border: #e2e8f0;
            --accent: #f59e0b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2.5rem 1rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 820px;
            margin: 0 auto;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            padding: 2.5rem;
        }}
        .header-brand {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--primary);
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        h1 {{
            font-size: 1.75rem;
            color: var(--text);
            margin: 0 0 1rem 0;
            line-height: 1.35;
        }}
        .meta-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 2rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            background: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
        }}
        .badge-primary {{
            background: #dbeafe;
            color: #1e40af;
            border-color: #bfdbfe;
        }}
        .content-box {{
            background: #fafafa;
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .section-heading {{
            font-size: 1.1rem;
            margin: 0 0 1rem 0;
            color: var(--primary);
        }}
        .content-body {{
            font-size: 0.98rem;
            white-space: pre-wrap;
            margin: 0;
            color: #334155;
            line-height: 1.65;
        }}
        .warning-box {{
            border-left-color: var(--accent);
            background: #fffbeb;
        }}
        .content-warning {{
            color: #92400e;
            margin: 0;
        }}
        .actions {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .action-buttons {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}
        .btn-official {{
            display: inline-flex;
            align-items: center;
            padding: 0.75rem 1.25rem;
            background: var(--primary);
            color: #ffffff;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.95rem;
            transition: background 0.2s ease;
        }}
        .btn-official:hover {{
            background: var(--primary-hover);
        }}
        .btn-archive {{
            display: inline-flex;
            align-items: center;
            padding: 0.75rem 1.25rem;
            background: #475569;
            color: #ffffff;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.95rem;
            transition: background 0.2s ease;
        }}
        .btn-archive:hover {{
            background: #334155;
        }}
        .footnote {{
            font-size: 0.85rem;
            color: var(--muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-brand">IP-SAKTI Sahayak · Local Source Document Viewer</div>
        <h1>{title}</h1>
        <div class="meta-bar">
            <span class="badge badge-primary">{authority}</span>
            <span class="badge">TYPE: {doc_type}</span>
            <span class="badge">SCOPE: {jurisdiction}</span>
            <span class="badge">ID: {canonical_sid}</span>
        </div>
        {content_html}
        <div class="actions">
            <div class="action-buttons">
                {official_link_html}
                {archive_link_html}
            </div>
            <div class="footnote">Grounded in local knowledge base archive</div>
        </div>
    </div>
</body>
</html>"""

    return HTMLResponse(content=html_content)


