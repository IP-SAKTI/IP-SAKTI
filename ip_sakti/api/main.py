"""
ip_sakti.api.main — FastAPI application server for IP-SAKTI Sahayak.

Provides REST API endpoints for /health, /query, and /document/{source_id}.
"""

import html
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Header, Query, Response, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from ip_sakti.api.schemas import (
    APIQueryRequest,
    APIQueryResponse,
    HealthResponse,
    RegisterRequest,
    LoginRequest,
    MagicLinkRequest,
    MagicLinkResponse,
    AuthResponse,
    ProfileUpdateRequest,
    ContactRequest,
    ContactResponse,
    SaveHistoryRequest,
)
from ip_sakti.models.query import FormulationCategory, Jurisdiction, QueryRequest, SourceViewerResponse
from ip_sakti.retrieval.sources import SourceRegistry
from ip_sakti.service import IPSAKTIService
from ip_sakti.utils.auth import AuthService
from ip_sakti.utils.chat_storage import ChatStorageService

logger = logging.getLogger(__name__)

# Singleton service instances
service: IPSAKTIService | None = None
_auth_service: AuthService | None = None
_chat_storage_service: ChatStorageService | None = None


def get_service() -> IPSAKTIService:
    """Return initialised IPSAKTIService instance."""
    global service
    if service is None:
        service = IPSAKTIService()
    return service


def get_auth_service() -> AuthService:
    """Return initialised AuthService instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def get_chat_storage_service() -> ChatStorageService:
    """Return initialised ChatStorageService instance."""
    global _chat_storage_service
    if _chat_storage_service is None:
        _chat_storage_service = ChatStorageService()
    return _chat_storage_service


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

    from ip_sakti.models.query import ConversationMessageModel, SearchMode
    sm_enum = SearchMode.HYBRID
    try:
        sm_enum = SearchMode(payload.search_mode.lower())
    except (ValueError, AttributeError):
        logger.debug(f"Unrecognised search_mode '{payload.search_mode}', defaulting to HYBRID.")

    history_models = [
        ConversationMessageModel(role=m.get("role", "user"), content=m.get("content", ""))
        for m in payload.conversation_history
        if isinstance(m, dict) and "content" in m
    ]

    query_req = QueryRequest(
        raw_query=payload.raw_query,
        jurisdiction=j_enum,
        formulation_category=f_enum,
        user_language=payload.user_language,
        conversation_id=payload.conversation_id,
        conversation_history=history_models,
        search_mode=sm_enum,
        user_id=payload.user_id,
    )


    try:
        srv = get_service()
        final_resp = srv.process_query(query_req)

        agents_str = [a.value for a in final_resp.agents_invoked]

        logger.info(
            f"[IP-SAKTI RUNTIME answerability-fix-v2] Query: {query_req.raw_query!r} | "
            f"IsAbstention: {final_resp.is_abstention} | EvidenceCount: {len(final_resp.evidence)}"
        )

        # Extract canonical float confidence score and Bayesian metadata
        conf_score = None
        conf_pct = None
        conf_lvl = None
        conf_abstain = final_resp.is_abstention
        conf_signals = {}

        if final_resp.confidence:
            conf_score = float(final_resp.confidence.score)
            conf_pct = getattr(final_resp.confidence, "confidence_percentage", round(conf_score * 100.0, 2))
            if conf_pct is None:
                conf_pct = round(conf_score * 100.0, 2)
            conf_lvl = getattr(final_resp.confidence, "confidence_level", "MEDIUM") or "MEDIUM"
            conf_abstain = getattr(final_resp.confidence, "below_threshold", final_resp.is_abstention)
            conf_signals = getattr(final_resp.confidence, "signals", {}) or {}

        # Extract actual vector cosine similarity score from FAISS retrieval evidence
        cosine_sim = None
        if final_resp.evidence:
            faiss_scores = [ev.faiss_score for ev in final_resp.evidence if ev.faiss_score is not None]
            if faiss_scores:
                cosine_sim = float(max(faiss_scores))

        logger.info(
            f"[RETRIEVAL_SCORE_DEBUG] query_id={final_resp.query_id} "
            f"evidence_count={len(final_resp.evidence)} "
            f"faiss_scores={[round(ev.faiss_score, 4) for ev in final_resp.evidence if ev.faiss_score is not None]}"
        )
        logger.info(f"[CANONICAL_COSINE] raw_cosine_similarity={cosine_sim}")
        logger.info(
            f"[CONFIDENCE] raw_cosine={cosine_sim} "
            f"confidence_score={conf_score} "
            f"confidence_percentage={conf_pct}% "
            f"confidence_level={conf_lvl}"
        )

        return APIQueryResponse(
            query_id=final_resp.query_id,
            answer=final_resp.answer,
            is_abstention=final_resp.is_abstention,
            confidence=conf_score,
            cosine_similarity=cosine_sim,
            confidence_score=conf_score,
            confidence_percentage=conf_pct,
            confidence_level=conf_lvl,
            confidence_should_abstain=conf_abstain,
            confidence_signals=conf_signals,
            evidence=final_resp.evidence,
            citations=final_resp.citations,
            agents_invoked=agents_str,
            disclaimer=final_resp.disclaimer,
            search_mode=final_resp.search_mode.value if hasattr(final_resp.search_mode, "value") else str(final_resp.search_mode),
            live_research_metadata=final_resp.live_research_metadata,
            detected_language=getattr(final_resp, "detected_language", "en"),
            original_query=getattr(final_resp, "original_query", payload.raw_query),
            normalized_english_query=getattr(final_resp, "normalized_english_query", None),
            answer_language=getattr(final_resp, "response_language", "en"),
        )

    except Exception as exc:
        logger.error(f"Error processing query in API endpoint: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while processing the query: {exc}",
        )


# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=AuthResponse, tags=["Authentication"])
async def register(payload: RegisterRequest) -> AuthResponse:
    """Register new user account."""
    auth_srv = get_auth_service()
    user_data, error_msg = auth_srv.register_user(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        confirm_password=payload.confirm_password or payload.password,
        terms_accepted=payload.terms_accepted,
    )
    if error_msg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    token = user_data.get("access_token") or ""
    return AuthResponse(user=user_data, token=token, message="Registration successful.")


@app.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
async def login(payload: LoginRequest) -> AuthResponse:
    """Authenticate existing user credentials."""
    auth_srv = get_auth_service()
    user_data, error_msg = auth_srv.authenticate_user(email=payload.email, password=payload.password)
    if error_msg:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg)

    token = user_data.get("access_token") or ""
    return AuthResponse(user=user_data, token=token, message="Login successful.")


@app.post("/auth/magic-link", response_model=MagicLinkResponse, tags=["Authentication"])
async def send_magic_link(payload: MagicLinkRequest) -> MagicLinkResponse:
    """
    Send a Supabase Magic Link OTP email for passwordless authentication.

    The user receives an email with a one-time link.  Clicking that link
    redirects them to ``payload.redirect_to`` (default: ``/auth/callback``)
    with ``#access_token=...&type=magiclink`` in the URL hash.
    The frontend callback page exchanges these tokens via ``GET /auth/verify``.
    """
    auth_srv = get_auth_service()
    ok, error_msg = auth_srv.send_magic_link(
        email=payload.email,
        redirect_to=payload.redirect_to,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    return MagicLinkResponse(
        status="sent",
        message="Magic link sent. Please check your email and click the link to sign in.",
    )


@app.get("/auth/verify", response_model=AuthResponse, tags=["Authentication"])
async def verify_token(authorization: Optional[str] = Header(default=None)) -> AuthResponse:
    """Verify Supabase Auth session token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided")

    token = authorization.split("Bearer ")[1].strip()
    auth_srv = get_auth_service()
    user_data = auth_srv.verify_session(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token")

    return AuthResponse(user=user_data, token=token, message="Session valid.")


@app.post("/auth/logout", tags=["Authentication"])
async def logout_user(authorization: Optional[str] = Header(default=None)):
    """Sign out user session from Supabase Auth."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        auth_srv = get_auth_service()
        auth_srv.sign_out(token)
    return {"message": "Logged out successfully."}


# ---------------------------------------------------------------------------
# Research History endpoints
# ---------------------------------------------------------------------------

@app.get("/history", tags=["Research History"])
async def get_history(user_id: Optional[str] = Query(default=None), limit: int = 50):
    """Retrieve user research history."""
    chat_srv = get_chat_storage_service()
    return chat_srv.list_conversations(user_id=user_id, limit=limit)


@app.get("/history/{conversation_id}", tags=["Research History"])
async def get_history_detail(conversation_id: str, user_id: Optional[str] = Query(default=None)):
    """Retrieve detailed message history for a single conversation."""
    chat_srv = get_chat_storage_service()
    conv = chat_srv.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or access denied")
    if user_id and conv.get("user_id") and conv.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return conv


@app.post("/history", tags=["Research History"])
async def save_history(payload: SaveHistoryRequest):
    """Save or update a research query in history."""
    chat_srv = get_chat_storage_service()
    conv = chat_srv.create_conversation(
        title=payload.title, conversation_id=payload.id, user_id=payload.user_id
    )
    if payload.query:
        chat_srv.add_message(
            conversation_id=payload.id,
            role="user",
            content=payload.query,
            user_id=payload.user_id,
        )
    if payload.response:
        content_text = payload.response.get("answer") if isinstance(payload.response, dict) else str(payload.response)
        chat_srv.add_message(
            conversation_id=payload.id,
            role="assistant",
            content=content_text,
            metadata={"response": payload.response},
            user_id=payload.user_id,
        )
    return {"status": "success", "conversation": conv}


@app.delete("/history/{conversation_id}", tags=["Research History"])
async def delete_history(conversation_id: str, user_id: Optional[str] = Query(default=None)):
    """Delete a research query record from history."""
    chat_srv = get_chat_storage_service()
    conv = chat_srv.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if user_id and conv and conv.get("user_id") and conv.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if hasattr(chat_srv, "delete_conversation"):
        chat_srv.delete_conversation(conversation_id=conversation_id, user_id=user_id)
    return {"status": "success", "id": conversation_id}


# ---------------------------------------------------------------------------
# Contact Support endpoint
# ---------------------------------------------------------------------------

@app.post("/contact", response_model=ContactResponse, tags=["Support"])
async def contact_support(payload: ContactRequest) -> ContactResponse:
    """Record contact support submission to Supabase PostgreSQL."""
    logger.info(f"Support message from {payload.name} ({payload.email}) regarding '{payload.subject}'")
    
    from ip_sakti.utils.supabase_client import SupabaseClient
    from uuid import uuid4
    from datetime import datetime, timezone
    
    sp_client = SupabaseClient()
    if sp_client.is_configured:
        try:
            sp_client.insert(
                table="support_inquiries",
                data={
                    "id": str(uuid4()),
                    "name": payload.name,
                    "email": payload.email,
                    "subject": payload.subject,
                    "message": payload.message,
                    "user_id": payload.user_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                use_service_role=True if sp_client.service_role_key else False,
            )
        except Exception as exc:
            logger.warning(f"Could not persist support inquiry to Supabase: {exc}")

    return ContactResponse(status="success", message="Your inquiry has been received. Our team will contact you shortly.")



# ---------------------------------------------------------------------------
# Speech-to-Text / Voice Input endpoint
# ---------------------------------------------------------------------------

@app.post("/transcribe", tags=["Voice Input"])
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None)
):
    """
    Accepts recorded audio file (webm, wav, m4a, mp3, ogg) and optional language hint
    and returns transcribed text using pretrained Whisper model.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No audio file provided.")

    try:
        content = await file.read()
        from ip_sakti.services.transcription import transcribe_audio_bytes
        res = transcribe_audio_bytes(
            content,
            filename=file.filename or "audio.webm",
            content_type=file.content_type,
            target_lang=language
        )
        return res
    except Exception as e:
        logger.error(f"Transcription API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}"
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


