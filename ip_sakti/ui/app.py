"""
ip_sakti.ui.app — Streamlit Web Interface for IP-SAKTI Sahayak.

Editorial-style multilingual interface for Traditional Knowledge,
Intellectual Property, AYUSH and Access & Benefit-Sharing research.

The UI communicates with the existing FastAPI backend. No retrieval,
orchestration, LLM, or database logic is implemented here.
"""

from __future__ import annotations

import base64
import html
import json
import logging
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path for Streamlit runner
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
import streamlit as st

# Cookie-based session persistence
try:
    import extra_streamlit_components as stx
    _COOKIES_AVAILABLE = True
except ImportError:
    _COOKIES_AVAILABLE = False

from ip_sakti.retrieval.sources import SourceRegistry
from ip_sakti.utils.auth import AuthService
from ip_sakti.utils.chat_storage import ChatStorageService
from ip_sakti.utils.session_manager import COOKIE_NAME, SessionManager

logger = logging.getLogger(__name__)


@st.cache_resource
def get_source_registry() -> SourceRegistry:
    """Return cached SourceRegistry instance for UI source lookup."""
    return SourceRegistry()


@st.cache_resource
def get_session_manager() -> SessionManager:
    """Return cached SessionManager instance for persistent auth sessions."""
    return SessionManager()


def get_chat_storage() -> ChatStorageService:
    """Return a fresh ChatStorageService instance per rerun."""
    return ChatStorageService()


@st.cache_resource
def get_auth_service() -> AuthService:
    """Return cached AuthService instance for authentication."""
    return AuthService()


def _get_cookie_manager():
    """Return a CookieManager if extra_streamlit_components is available.
    Caches the instance in st.session_state to prevent DuplicateWidgetID errors.
    """
    if not _COOKIES_AVAILABLE:
        return None
    if "_cookie_manager" not in st.session_state:
        try:
            st.session_state["_cookie_manager"] = stx.CookieManager(key="ipsakti_cookie_mgr")
        except Exception as err:
            logger.warning(f"Could not initialize CookieManager: {err}")
            return None
    return st.session_state["_cookie_manager"]


def initialize_authentication() -> None:
    """
    Restore authenticated session from persistent storage (URL query params / cookie)
    on every Streamlit rerun or browser refresh.

    Flow:
    1. If session_state already has authenticated_user → already active, skip.
    2. Check native Streamlit query_params for persistent session token.
    3. If not found, check persistent browser cookie if available.
    4. Validate the token against the server-side session store / Supabase Auth.
    5. If valid → restore authenticated_user in session_state.
    6. If invalid/absent → leave unauthenticated (show login page).
    """
    if st.session_state.get("authenticated_user") is not None:
        return  # Already authenticated in this session

    signed_token: Optional[str] = None

    # 1. Native Streamlit persistence via st.query_params (instant across Ctrl+R / browser reload)
    try:
        if "session" in st.query_params and st.query_params["session"]:
            signed_token = st.query_params["session"]
    except Exception:
        pass

    # 2. Browser cookie persistence if extra_streamlit_components is available
    if not signed_token and _COOKIES_AVAILABLE:
        cookie_manager = _get_cookie_manager()
        if cookie_manager is not None:
            signed_token = cookie_manager.get(COOKIE_NAME)

    if not signed_token:
        return

    session_mgr = get_session_manager()
    user_data = session_mgr.validate_session(signed_token)
    if not user_data:
        auth_svc = get_auth_service()
        user_data = auth_svc.verify_session(signed_token)

    if user_data:
        st.session_state.authenticated_user = user_data
        st.session_state["session_token"] = signed_token
        st.session_state["page"] = "dashboard"
        st.session_state.auth_page = "authenticated"
        try:
            st.query_params["session"] = signed_token
        except Exception:
            pass
        # Reset conversation so it loads fresh for this user
        if "active_conversation_id" not in st.session_state:
            st.session_state.active_conversation_id = None
        if "messages" not in st.session_state:
            st.session_state.messages = []
        logger.info(
            "Restored session from persistent token",
            extra={"user_id": user_data["id"]},
        )
    else:
        st.session_state.pop("session_token", None)
        # Token invalid/expired — clear stale params & cookie
        try:
            if "session" in st.query_params:
                del st.query_params["session"]
        except Exception:
            pass
        if _COOKIES_AVAILABLE:
            cookie_manager = _get_cookie_manager()
            if cookie_manager is not None:
                try:
                    cookie_manager.delete(COOKIE_NAME)
                except Exception:
                    pass


def md_html(content: str, sidebar: bool = False) -> None:
    """Render multi-line HTML via st.markdown, safely dedented to avoid
    Markdown code-block leakage from Python source indentation."""
    target = st.sidebar if sidebar else st
    target.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)



def format_chat_date(date_str: str) -> str:
    """Format UTC ISO timestamp string into human-friendly relative date."""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if dt.date() == now.date():
            return "Today"
        elif (now.date() - dt.date()).days == 1:
            return "Yesterday"
        else:
            return dt.strftime("%b %d")
    except Exception:
        return ""


def get_chat_icon(title: str) -> str:
    """Return relevant emoji icon based on conversation title."""
    t_lower = title.lower()
    if "patent" in t_lower:
        return "📄"
    elif "form" in t_lower or "licens" in t_lower or "24d" in t_lower:
        return "⚖️"
    elif "tkdl" in t_lower or "tradition" in t_lower or "ayurved" in t_lower or "herb" in t_lower:
        return "🌿"
    elif "abs" in t_lower or "biodiversity" in t_lower or "nba" in t_lower:
        return "🏛️"
    return "💬"



# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="IP-SAKTI Sahayak",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000",
)

APP_VERSION = "v0.1.0"

ASSET_DIR = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSET_DIR / "ip_sakti_sahayak.png"


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

def inject_styles() -> None:
    """Apply the visual system for the IP-SAKTI interface matching reference screenshot EXACTLY."""

    md_html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

        :root {
            --forest-deep: #003E29;
            --forest-mid: #044D34;
            --forest-accent: #195941;
            --parchment: #EEF3E4;
            --card-bg: #FAFDF6;
            --card-border: #C8D7C2;
            --ink-dark: #003E29;
            --ink-muted: #385246;
            --text-light: #E2EFE9;
            --text-muted-light: #7B9F8E;
        }

        /* Main application background */
        .stApp,
        div[data-testid="stAppViewContainer"] {
            background-color: var(--parchment) !important;
            color: var(--ink-dark);
            font-family: 'IBM Plex Sans', sans-serif !important;
            overflow-y: auto !important;
        }

        .main .block-container {
            max-width: 1100px !important;
            padding-top: 1.2rem !important;
            padding-bottom: 5rem !important;
            position: relative !important;
            z-index: 1 !important;
        }

        /* Remove default Streamlit top header & footer */
        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
        }
        header[data-testid="stHeader"] > div {
            display: none !important;
        }
        footer {
            visibility: hidden !important;
        }

        button[title="View fullscreen"],
        [data-testid="StyledFullScreenButton"],
        [data-testid="stElementToolbar"],
        button[aria-label="View fullscreen"],
        .stElementToolbar {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: var(--forest-deep) !important;
            border-right: none !important;
            width: 270px !important;
        }

        section[data-testid="stSidebar"] > div {
            background-color: var(--forest-deep) !important;
            padding: 1.4rem 1.1rem !important;
        }

        section[data-testid="stSidebar"] * {
            color: var(--text-light);
            font-family: 'IBM Plex Sans', sans-serif !important;
        }

        /* Sidebar New Chat Button */
        button[key="btn_new_chat"],
        section[data-testid="stSidebar"] button[key="btn_new_chat"] {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid #1E5C46 !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            padding: 0.5rem 0.8rem !important;
            min-height: 42px !important;
            text-align: center !important;
            margin-bottom: 1rem !important;
            transition: all 0.2s ease !important;
        }

        button[key="btn_new_chat"]:hover {
            background: #0A4F37 !important;
            border-color: #519E7E !important;
        }

        /* Sidebar Search Box */
        section[data-testid="stSidebar"] div[data-testid="stTextInput"] input {
            background-color: #003322 !important;
            border: 1px solid #1E5C46 !important;
            border-radius: 8px !important;
            color: #E2EFE9 !important;
            font-size: 0.82rem !important;
            height: 36px !important;
            padding: 0 0.8rem !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stTextInput"] input::placeholder {
            color: #7B9F8E !important;
        }

        /* Sidebar Chat History Buttons */
        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
            gap: 0.2rem !important;
            margin-bottom: 0.25rem !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button {
            background: transparent !important;
            border: none !important;
            color: #CBE0D6 !important;
            font-size: 0.82rem !important;
            padding: 0.35rem 0.5rem !important;
            min-height: 34px !important;
            border-radius: 6px !important;
            text-align: left !important;
            box-shadow: none !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button:hover {
            background: #0A4F37 !important;
            color: #FFFFFF !important;
        }

        /* Bottom Sidebar Buttons */
        button[key="sb_btn_settings"],
        button[key="sb_btn_logout"] {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid #1E5C46 !important;
            color: #E2EFE9 !important;
            border-radius: 8px !important;
            font-size: 0.84rem !important;
            min-height: 38px !important;
            margin-top: 0.4rem !important;
        }

        button[key="sb_btn_settings"]:hover,
        button[key="sb_btn_logout"]:hover {
            background: #0A4F37 !important;
            border-color: #519E7E !important;
        }

        /* Top Right User Profile Pill Styling */
        div[data-testid="stExpander"] {
            background: #FAFDF6 !important;
            border: 1px solid #C8D7C2 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
            margin-bottom: 0 !important;
        }

        div[data-testid="stExpander"] summary {
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            color: #003E29 !important;
            padding: 0.4rem 0.8rem !important;
        }

        /* Hero Section Typography */
        .hero-tagline {
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-style: italic;
            font-size: 1.25rem;
            color: #003E29;
            margin-bottom: 0.6rem;
            margin-top: 0.6rem;
        }

        .hero-heading {
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 3.6rem;
            font-weight: 600;
            color: #003E29;
            letter-spacing: -0.025em;
            line-height: 1.05;
            margin-bottom: 1.1rem;
        }

        .hero-subtext {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 1.05rem;
            line-height: 1.65;
            color: #385246;
            max-width: 820px;
            margin-bottom: 2.2rem;
        }

        /* Botanical Overlay Layers */
        .botanical-bg-container {
            position: fixed;
            top: 0;
            left: 270px;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }

        .botanical-leaf {
            position: absolute;
            pointer-events: none;
        }

        .bot-top-left {
            top: -40px;
            left: -20px;
            opacity: 0.82;
        }

        .bot-top-right {
            top: -50px;
            right: -30px;
            opacity: 0.85;
        }

        .bot-bottom-left {
            bottom: -30px;
            left: -20px;
            opacity: 0.82;
        }

        .bot-bottom-right {
            bottom: -40px;
            right: -30px;
            opacity: 0.88;
        }

        .bot-float-1 {
            top: 140px;
            right: 280px;
            opacity: 0.55;
            transform: rotate(25deg);
        }

        /* Feature Cards Grid */
        .feature-card {
            background: #FAFDF6;
            border: 1px solid #C8D7C2;
            border-left: 4px solid #003E29;
            border-radius: 10px;
            padding: 1.3rem 1.4rem;
            min-height: 145px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
            transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
        }

        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
            background: #F4FAF0;
        }

        .feature-card-title {
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 1.22rem;
            font-weight: 700;
            color: #003E29;
        }

        .feature-card-copy {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.86rem;
            line-height: 1.55;
            color: #4A6357;
            margin-top: 0.5rem;
        }

        /* Feature Card Action Buttons */
        .feature-card-btn button {
            background: #FAFDF6 !important;
            border: 1px solid #C8D7C2 !important;
            border-left: 4px solid #003E29 !important;
            border-radius: 10px !important;
            padding: 1rem 1.2rem !important;
            min-height: 145px !important;
            text-align: left !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
            transition: all 0.2s ease !important;
        }

        .feature-card-btn button:hover {
            transform: translateY(-2px) !important;
            background: #F4FAF0 !important;
            border-color: #003E29 !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06) !important;
        }

        /* Chat Input Styling */
        [data-testid="stBottom"],
        div[data-testid="stChatInput"] {
            background: transparent !important;
            border: none !important;
        }

        div[data-testid="stChatInput"] > div {
            background: #FFFFFF !important;
            border: 1px solid #C8D7C2 !important;
            border-radius: 10px !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important;
            padding: 4px 6px !important;
        }

        div[data-testid="stChatInput"] textarea {
            color: #003E29 !important;
            font-size: 0.92rem !important;
            font-family: 'IBM Plex Sans', sans-serif !important;
        }

        div[data-testid="stChatInput"] button {
            background: #003E29 !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
            width: 42px !important;
            height: 42px !important;
        }

        /* User Message Wrapper */
        .user-message-wrapper {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            margin: 0.6rem 0 1.4rem auto;
            max-width: 80%;
        }

        .user-message-author {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.72rem;
            font-weight: 600;
            color: #003E29;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            text-align: right;
        }

        .user-message-body {
            background: #FAFDF6;
            border: 1px solid #C8D7C2;
            border-radius: 8px;
            padding: 0.85rem 1.15rem;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.96rem;
            line-height: 1.6;
            color: #003E29 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            word-break: break-word;
        }

        /* Assistant Response Card */
        .response-label {
            margin-top: 0.4rem;
            margin-bottom: 0.65rem;
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 1.45rem;
            font-weight: 600;
            color: #003E29;
            letter-spacing: -0.01em;
        }

        .response-text {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.96rem;
            line-height: 1.75;
            color: #263A35;
            margin-bottom: 1.4rem;
        }

        .evidence-card {
            margin: 0.8rem 0;
            padding: 0.95rem 1.15rem;
            border: 1px solid #C8D7C2;
            border-radius: 8px;
            background: #FAFDF6;
        }

        .evidence-title {
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 1.05rem;
            font-weight: 600;
            color: #003E29;
            margin-bottom: 0.25rem;
        }
        </style>
        """
    )


# ---------------------------------------------------------------------------
# Backend communication
# ---------------------------------------------------------------------------

def query_backend_api(
    raw_query: str,
    jurisdiction: str,
    formulation_category: str,
    user_language: Optional[str],
    api_base_url: str,
    conversation_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Send the user request to the existing FastAPI /query endpoint,
    falling back to direct Python pipeline execution if unreachable.
    """
    url = f"{api_base_url.rstrip('/')}/query"

    payload = {
        "raw_query": raw_query,
        "jurisdiction": jurisdiction,
        "formulation_category": formulation_category,
        "user_language": (
            user_language if user_language != "auto" else None
        ),
        "conversation_id": conversation_id,
        "conversation_history": conversation_history or [],
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.HTTPStatusError):
        # Fallback to direct Python service call when FastAPI server is not active
        from ip_sakti.service import IPSAKTIService
        from ip_sakti.models.query import (
            QueryRequest,
            Jurisdiction,
            FormulationCategory,
            ConversationMessageModel,
        )

        j_enum = Jurisdiction(jurisdiction.lower()) if jurisdiction in Jurisdiction._value2member_map_ else Jurisdiction.UNKNOWN
        f_enum = FormulationCategory(formulation_category.lower()) if formulation_category in FormulationCategory._value2member_map_ else FormulationCategory.UNKNOWN
        hist_models = [
            ConversationMessageModel(role=m.get("role", "user"), content=m.get("content", ""))
            for m in (conversation_history or [])
            if isinstance(m, dict) and "content" in m
        ]
        q_req = QueryRequest(
            raw_query=raw_query,
            jurisdiction=j_enum,
            formulation_category=f_enum,
            user_language=user_language if user_language != "auto" else None,
            conversation_id=conversation_id,
            conversation_history=hist_models,
        )
        srv = IPSAKTIService()
        res = srv.process_query(q_req)
        return res.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar(
    chat_storage: ChatStorageService,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Render the dark forest green sidebar matching the reference screenshot EXACTLY."""

    # Top Branding & Logo
    logo_b64 = get_logo_base64()
    if logo_b64:
        md_html(
            f"""\
            <div style="text-align: center; margin-bottom: 0.8rem;">
              <img src="data:image/png;base64,{logo_b64}" alt="IP-SAKTI Sahayak" style="width: 82px; height: auto; display: block; margin: 0 auto 0.4rem auto;" />
              <div style="font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.3rem; font-weight: 700; color: #FFFFFF; letter-spacing: 0.02em;">
                IP-SAKTI
              </div>
              <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 0.82rem; color: #A1C9B6; margin-top: -0.15rem;">
                Sahayak
              </div>
              <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72rem; color: #7B9F8E; margin-top: 0.35rem; letter-spacing: 0.03em;">
                Traditional Knowledge · IP · AYUSH
              </div>
            </div>
            """,
            sidebar=True,
        )
    else:
        md_html(
            """\
            <div style="text-align: center; margin-bottom: 0.8rem;">
              <div style="font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.35rem; font-weight: 700; color: #FFFFFF;">
                IP-SAKTI
              </div>
              <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 0.85rem; color: #A1C9B6;">
                Sahayak
              </div>
              <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72rem; color: #7B9F8E; margin-top: 0.3rem;">
                Traditional Knowledge · IP · AYUSH
              </div>
            </div>
            """,
            sidebar=True,
        )

    # 1. New Chat Button
    if st.sidebar.button("+  New Chat", key="btn_new_chat", use_container_width=True):
        new_conv = chat_storage.create_conversation("New Chat", user_id=user_id)
        st.session_state.active_conversation_id = new_conv["id"]
        st.session_state.messages = []
        st.rerun()

    # 2. History Section Header
    md_html(
        '<div style="font-family: \'IBM Plex Sans\', sans-serif; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #7B9F8E; margin-top: 1rem; margin-bottom: 0.4rem;">HISTORY</div>',
        sidebar=True,
    )

    # 3. Search History Input Box
    search_query = st.sidebar.text_input(
        "Search history",
        key="sb_chat_search",
        placeholder="🔍 Search history...",
        label_visibility="collapsed",
    )

    conv_list = chat_storage.list_conversations(user_id=user_id, limit=40)
    active_cid = st.session_state.get("active_conversation_id")

    if search_query and search_query.strip():
        sq = search_query.strip().lower()
        conv_list = [c for c in conv_list if sq in c.get("title", "").lower()]

    if conv_list:
        show_all = st.session_state.get("show_more_chats", False)
        display_convs = conv_list if show_all else conv_list[:8]

        for conv in display_convs:
            cid = conv["id"]
            title = conv["title"]
            is_active = (cid == active_cid)

            c_col, d_col = st.sidebar.columns([0.84, 0.16])

            active_symbol = "💬 "
            btn_text = f"{active_symbol}{title}"

            with c_col:
                if st.button(
                    btn_text,
                    key=f"chat_sel_{cid}",
                    use_container_width=True,
                    help=title,
                ):
                    st.session_state.active_conversation_id = cid
                    c_data = chat_storage.get_conversation(cid, user_id=user_id)
                    if c_data and "messages" in c_data:
                        restored = []
                        for m in c_data["messages"]:
                            role = m["role"]
                            content = m["content"]
                            meta = m.get("metadata")
                            if role == "assistant" and meta and isinstance(meta, dict):
                                restored.append({"role": role, "content": meta})
                            elif role == "assistant" and isinstance(content, str) and content.startswith("{"):
                                try:
                                    restored.append({"role": role, "content": json.loads(content)})
                                except Exception:
                                    restored.append({"role": role, "content": content})
                            else:
                                restored.append({"role": role, "content": content})
                        st.session_state.messages = restored
                    else:
                        st.session_state.messages = []
                    st.rerun()

            with d_col:
                if st.button("🗑️", key=f"chat_del_{cid}", help="Delete conversation"):
                    chat_storage.delete_conversation(cid, user_id=user_id)
                    if cid == st.session_state.get("active_conversation_id"):
                        rem = chat_storage.list_conversations(user_id=user_id, limit=1)
                        if rem:
                            st.session_state.active_conversation_id = rem[0]["id"]
                            rem_data = chat_storage.get_conversation(rem[0]["id"], user_id=user_id)
                            st.session_state.messages = rem_data.get("messages", []) if rem_data else []
                        else:
                            new_c = chat_storage.create_conversation("New Chat", user_id=user_id)
                            st.session_state.active_conversation_id = new_c["id"]
                            st.session_state.messages = []
                    st.rerun()

        if len(conv_list) > 8 and not show_all:
            if st.sidebar.button("Show more chats...", key="btn_show_more", use_container_width=True):
                st.session_state.show_more_chats = True
                st.rerun()

    md_html("<div style='height: 1.5rem;'></div>", sidebar=True)

    # 4. Settings & Logout Buttons at bottom
    if st.sidebar.button("⚙️ Settings", key="sb_btn_settings", use_container_width=True):
        st.session_state.show_settings = True
        st.rerun()

    if st.sidebar.button("🚪 Logout", key="sb_btn_logout", use_container_width=True):
<<<<<<< HEAD
        # Revoke persistent session + delete cookie + clear query params
        try:
            if "session" in st.query_params:
                del st.query_params["session"]
        except Exception:
            pass
=======
>>>>>>> 874b31c (feat(ui): recreate frontend UI to match reference screenshot exactly)
        cookie_manager = _get_cookie_manager()
        if cookie_manager is not None:
            signed_token = cookie_manager.get(COOKIE_NAME)
            if signed_token:
                get_session_manager().revoke_session(signed_token)
            try:
                cookie_manager.delete(COOKIE_NAME, key="sb_logout_cookie_del")
            except Exception:
                pass
        st.session_state.pop("session_token", None)
        st.session_state.authenticated_user = None
        st.session_state.active_conversation_id = None
        st.session_state.messages = []
        st.session_state.auth_page = "login"
        st.session_state["page"] = "login"
        if "_cookie_manager" in st.session_state:
            del st.session_state["_cookie_manager"]
        st.rerun()

    md_html(
        f"""
        <div class="sidebar-version">
            IP-SAKTI Sahayak {APP_VERSION}
        </div>
        """,
        sidebar=True,
    )

    return {
        "jurisdiction": "unknown",
        "formulation": "unknown",
        "user_lang": "auto",
        "api_url": DEFAULT_API_BASE_URL,
    }


# ---------------------------------------------------------------------------
# Message rendering
# ---------------------------------------------------------------------------

def render_user_message(text: str) -> None:
    """Render a clean, editorial user query block."""

    escaped_text = html.escape(text)
    md_html(
        f"""
        <div class="user-message-wrapper">
            <div class="user-message-author">You</div>
            <div class="user-message-body">{escaped_text}</div>
        </div>
        """
    )


def render_response(res: Dict[str, Any], filters: Dict[str, Any] | None = None) -> None:
    """Render an actual backend response."""

    filters_dict = filters or {}

    is_abstention = res.get("is_abstention", False)
    answer = res.get("answer", "")
    confidence = res.get("confidence")
    evidence = res.get("evidence", [])
    agents_invoked = res.get("agents_invoked", [])
    disclaimer = res.get("disclaimer", "")

    # ---------------------------------------------------------------
    # Lightweight status line
    # ---------------------------------------------------------------

    agent_text = (
        ", ".join(agents_invoked)
        if agents_invoked
        else "Not specified"
    )

    if is_abstention:
        confidence_text = "—"
    elif confidence and "score" in confidence:
        confidence_text = f"{confidence['score'] * 100:.0f}%"
    else:
        confidence_text = "—"

    status_text = (
        "Safe abstention"
        if is_abstention
        else "Source-grounded response"
    )

    md_html(
        f"""
        <div class="status-line">
            <span><strong class="status-label">Status</strong> · {status_text}</span>
            <span class="status-sep">|</span>
            <span><strong class="status-label">Confidence</strong> · {confidence_text}</span>
            <span class="status-sep">|</span>
            <span><strong class="status-label">Agents</strong> · {agent_text}</span>
        </div>
        """
    )

    # ---------------------------------------------------------------
    # Answer
    # ---------------------------------------------------------------

    if is_abstention:
        md_html('<div class="response-label">Unable to provide a reliable conclusion</div>')

        md_html(f'<div class="response-text">{answer}</div>')

        md_html(
            """
            <div class="facilitator-box">
                <div class="facilitator-title">
                    Human / IP Facilitator Pathway
                </div>
                <div class="facilitator-copy">
                    This query has been identified as requiring additional
                    human review. The existing safe-abstention pathway
                    records the escalation for domain-expert consideration.
                </div>
            </div>
            """
        )

    else:
        md_html('<div class="response-label">Response</div>')

        md_html(f'<div class="response-text">{answer}</div>')

    # ---------------------------------------------------------------
    # Confidence details
    # ---------------------------------------------------------------

    if confidence and not is_abstention:
        with st.expander("Confidence & verification", expanded=False):

            m1, m2, m3, m4 = st.columns(4)

            m1.metric(
                "Overall score",
                f"{confidence.get('score', 0) * 100:.1f}%",
            )

            m2.metric(
                "Evidence",
                confidence.get("evidence_count", 0),
            )

            m3.metric(
                "Citation coverage",
                f"{confidence.get('citation_coverage', 0) * 100:.0f}%",
            )

            m4.metric(
                "Rerank score",
                f"{confidence.get('avg_rerank_score', 0):.2f}",
            )

            reason = confidence.get("reason")

            if reason:
                st.caption(reason)

    # ---------------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------------

    if evidence and not is_abstention:

        with st.expander(
            f"Sources & evidence · {len(evidence)}",
            expanded=False,
        ):

            for i, chunk in enumerate(evidence, 1):

                label = chunk.get(
                    "source_label",
                    f"[SOURCE_{i}]",
                )

                title = chunk.get(
                    "title",
                    "Untitled document",
                )

                source_name = chunk.get(
                    "source_name",
                    "Unknown source",
                )

                authority = chunk.get(
                    "authority",
                    "Not specified",
                )

                content = chunk.get(
                    "content",
                    "",
                )

                # Prefer /document/{source_id} API redirect (allowlist-controlled).
                # Falls back to raw source_url if no doc_id is available.
                source_id_val = chunk.get("source_id") or chunk.get("doc_id", "")
                api_url = filters_dict.get("api_url", DEFAULT_API_BASE_URL)
                if source_id_val:
                    doc_link = f"{api_url.rstrip('/')}/document/{source_id_val}"
                else:
                    doc_link = chunk.get("source_url")

                logger.info(
                    "Source document link generated",
                    extra={
                        "source_id": source_id_val,
                        "doc_id": chunk.get("doc_id"),
                        "api_url": api_url,
                        "document_url": doc_link,
                    },
                )

                md_html(
                    f"""
                    <div class="evidence-card">
                        <div class="evidence-title">
                            {label} · {title}
                        </div>
                        <div class="evidence-meta">
                            {source_name} · {authority}
                        </div>
                        <div class="evidence-content">
                            {content}
                        </div>
                    </div>
                    """
                )

                # Resolve source metadata from registry if available
                source_meta = get_source_registry().get_source(source_id_val) if source_id_val else None
                official_url = source_meta.url if source_meta else chunk.get("source_url")
                archive_url = source_meta.archive_url if (source_meta and source_meta.archive_url) else chunk.get("archive_url")

                links_html = []
                if doc_link:
                    links_html.append(
                        f'<a href="{doc_link}" target="_blank" rel="noopener noreferrer" '
                        f'style="color: #2563eb; font-weight: 600; text-decoration: underline;">'
                        f'📄 View Source Document</a>'
                    )
                if official_url and official_url.startswith("http"):
                    links_html.append(
                        f'<a href="{official_url}" target="_blank" rel="noopener noreferrer" '
                        f'style="color: #059669; font-weight: 600; text-decoration: underline;">'
                        f'🌐 Open Official Source</a>'
                    )
                if archive_url and archive_url.startswith("https://web.archive.org/"):
                    links_html.append(
                        f'<a href="{archive_url}" target="_blank" rel="noopener noreferrer" '
                        f'style="color: #4b5563; font-weight: 600; text-decoration: underline;">'
                        f'🏛️ View Archived Source</a>'
                    )

                if links_html:
                    links_joined = " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(links_html)
                    md_html(
                        f'<div style="margin-top: 0.35rem; margin-bottom: 1.25rem; font-size: 0.9rem;">'
                        f'{links_joined}</div>'
                    )

    # ---------------------------------------------------------------
    # Disclaimer
    # ---------------------------------------------------------------

    if disclaimer:
        md_html(f'<div class="disclaimer-text">{disclaimer}</div>')


# ---------------------------------------------------------------------------
# Authentication UI & User Management
# ---------------------------------------------------------------------------

def render_header_user_profile(user: Dict[str, Any]) -> None:
    """Render top header user profile control."""
    name = user.get("name", "User")
    email = user.get("email", "")
    initial = name[0].upper() if name else "U"
    # Truncate display name to keep expander label on one line
    display_name = name if len(name) <= 18 else name[:16] + "…"

    h_col1, h_col2 = st.columns([0.78, 0.22])
    with h_col2:
        with st.expander(f"👤 {display_name}", expanded=False):
            st.markdown(f"**{name}**")
            st.caption(email)
            st.markdown("---")
            if st.button("⚙️ Settings", key="hdr_btn_settings", use_container_width=True):
                st.session_state.show_settings = True
                st.rerun()
            if st.button("🚪 Logout", key="hdr_btn_logout", use_container_width=True):
                # Revoke persistent session + delete cookie + clear query params
                try:
                    if "session" in st.query_params:
                        del st.query_params["session"]
                except Exception:
                    pass
                cookie_manager = _get_cookie_manager()
                if cookie_manager is not None:
                    signed_token = cookie_manager.get(COOKIE_NAME)
                    if signed_token:
                        get_session_manager().revoke_session(signed_token)
                    try:
                        cookie_manager.delete(COOKIE_NAME, key="hdr_logout_cookie_del")
                    except Exception:
                        pass
                st.session_state.pop("session_token", None)
                st.session_state.authenticated_user = None
                st.session_state.active_conversation_id = None
                st.session_state.messages = []
                st.session_state.auth_page = "login"
                st.session_state["page"] = "login"
                if "_cookie_manager" in st.session_state:
                    del st.session_state["_cookie_manager"]
                st.rerun()


def render_settings_view(user: Dict[str, Any]) -> None:
    """Render Account & Application Settings panel."""
    st.markdown("## ⚙️ Account & Settings")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Account Name:** {user.get('name', 'User')}")
        st.markdown(f"**Email Address:** {user.get('email', '')}")
    with col2:
        st.markdown(f"**User ID:** `{user.get('id', '')}`")
        st.markdown(f"**Member Since:** {user.get('created_at', '')[:10] if user.get('created_at') else 'N/A'}")
    st.markdown("---")
    if st.button("Close Settings", key="btn_close_settings"):
        st.session_state.show_settings = False
        st.rerun()


def get_logo_base64() -> str:
    """Return base64 string for ip_sakti_sahayak.png logo asset."""
    if LOGO_PATH.exists():
        try:
            with open(LOGO_PATH, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""


def render_left_panel() -> None:
    """Render reusable pure HTML/CSS Navy Left Brand Panel for Auth pages matching Target Spec."""
    logo_b64 = get_logo_base64()
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="IP-SAKTI Sahayak" style="width: 95px; max-width: 95px; height: auto; display: block; margin: 0 auto 0.65rem auto;" />'
        if logo_b64
        else '<div style="font-family: Georgia, serif; font-size: 1.4rem; font-weight: 700; color: #ffffff; text-align: center; margin-bottom: 0.5rem;">🌿 IP-SAKTI</div>'
    )

    panel_html = f"""\
<div style="background-color: #081c38; min-height: 100vh; min-height: 100dvh; height: 100%; padding: 2rem 1.25rem; display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; box-sizing: border-box; color: #ffffff; overflow-y: auto;">
<div style="text-align: center; position: relative; z-index: 2; margin-bottom: 2rem;">
{logo_html}
<div style="font-family: sans-serif; font-size: 0.76rem; color: rgba(255,255,255,0.7); margin-bottom: 1rem; letter-spacing: 0.02em;">
Traditional Knowledge · IP · AYUSH
</div>
<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.15); margin: 1rem auto; width: 75%;">
<div style="font-family: Georgia, serif; font-style: italic; color: rgba(255,255,255,0.85); font-size: 0.85rem; line-height: 1.5; text-align: center; max-width: 190px; margin: 0 auto;">
Empowering the<br>Wisdom of Bharat<br>with Responsible AI
</div>
</div>

<svg width="120" height="140" viewBox="0 0 120 140" fill="none" xmlns="http://www.w3.org/2000/svg" style="position: absolute; bottom: 0px; left: 0px; opacity: 0.35; pointer-events: none; z-index: 1;">
<path d="M10 130 Q 30 90, 60 70 Q 90 50, 110 20" stroke="#7CB342" stroke-width="2.5" fill="none" />
<path d="M60 70 Q 40 50, 25 55 Q 35 75, 60 70 Z" fill="#7CB342" />
<path d="M80 50 Q 65 30, 50 35 Q 60 55, 80 50 Z" fill="#7CB342" />
<path d="M40 90 Q 20 75, 10 80 Q 20 95, 40 90 Z" fill="#7CB342" />
<path d="M25 110 Q 10 100, 2 105 Q 10 115, 25 110 Z" fill="#7CB342" />
</svg>
<svg width="160" height="180" viewBox="0 0 200 220" fill="none" xmlns="http://www.w3.org/2000/svg" style="position: absolute; bottom: 0px; right: 0px; opacity: 0.12; pointer-events: none; z-index: 1;">
<path d="M 70 10 L 90 15 L 110 10 L 130 25 L 140 45 L 160 55 L 180 70 L 170 90 L 150 105 L 135 120 L 120 145 L 110 170 L 95 195 L 85 210 L 80 190 L 75 160 L 65 140 L 50 130 L 35 115 L 25 95 L 30 75 L 45 60 L 55 40 Z" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-dasharray="3 3"/>
</svg>
</div>
"""
    md_html(panel_html)


def inject_auth_styles() -> None:
    """Inject Global CSS specifically for Auth pages (Login / Register)."""
    styles_html = """\
<style>
/* ---------------------------------------------------------------
   Global Viewport & Layout Overrides for Auth Pages Only
--------------------------------------------------------------- */

/* Hide Streamlit default header, footer, sidebar, floating fullscreen button, decoration strip */
header[data-testid="stHeader"],
footer,
section[data-testid="stSidebar"],
button[title="View fullscreen"],
[data-testid="StyledFullScreenButton"],
[data-testid="stElementToolbar"],
button[aria-label="View fullscreen"],
.stElementToolbar,
div[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Full viewport height & background with zero top padding */
html, body, #root, .stApp,
div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
div[data-testid="stMainBlockContainer"],
.main {
    background-color: #F5EFDC !important;
    width: 100% !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow-y: auto !important;
    top: 0 !important;
}

/* Remove default Streamlit block container padding */
.main .block-container,
div[data-testid="stMainBlockContainer"] {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    height: auto !important;
    margin: 0 !important;
}

/* Top-level columns container */
.main .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
    width: 100% !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    height: auto !important;
    gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Column 1 (Left Navy Panel ~29%) */
.main .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(1) {
    flex: 0 0 29% !important;
    max-width: 29% !important;
    min-width: 29% !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    height: 100% !important;
    background-color: #081c38 !important;
}

/* Column 2 (Right Cream Auth Panel ~71%) */
.main .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {
    flex: 0 0 71% !important;
    max-width: 71% !important;
    min-width: 71% !important;
    background-color: #F5EFDC !important;
    padding: 2rem 2rem 3rem 2rem !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    height: auto !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    box-sizing: border-box !important;
    overflow-y: auto !important;
}

/* Style .stTextInput input */
div[data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    border: 1px solid #d1d5db !important;
    font-size: 0.88rem !important;
    color: #111827 !important;
    height: 40px !important;
}

div[data-testid="stTextInput"] label {
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
    margin-bottom: 0.2rem !important;
}

/* Password Eye Icon integration & alignment */
div[data-testid="stTextInput"] button[aria-label*="password"],
div[data-testid="stTextInput"] button[title*="password"],
div[data-testid="stTextInput"] div[aria-hidden="true"] button,
div[data-testid="stTextInput"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    height: 38px !important;
    min-height: 38px !important;
    width: 36px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: #6b7280 !important;
}

/* Style primary form submit button */
div[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
    background-color: #1B4332 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    height: 42px !important;
    min-height: 42px !important;
    box-shadow: 0 1px 3px rgba(27,67,50,0.15) !important;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #143326 !important;
    color: #ffffff !important;
}

/* Style goto register/login link button */
button[key="btn_goto_register"],
button[key="btn_goto_login"],
div[data-testid="stElementContainer"] button[key="btn_goto_register"],
div[data-testid="stElementContainer"] button[key="btn_goto_login"] {
    background: transparent !important;
    border: none !important;
    color: #1B4332 !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    text-decoration: underline !important;
    padding: 0 !important;
    margin: 0.25rem auto 0 auto !important;
    box-shadow: none !important;
    height: auto !important;
    min-height: unset !important;
    width: auto !important;
    display: inline-block !important;
}

button[key="btn_goto_register"]:hover,
button[key="btn_goto_login"]:hover {
    color: #143326 !important;
    background: transparent !important;
}

/* Inner nested columns reset for 2-col inputs */
div[data-testid="stColumn"] div[data-testid="stHorizontalBlock"] {
    width: 100% !important;
    height: auto !important;
    gap: 0.75rem !important;
    align-items: center !important;
}

div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

/* Streamlit Checkbox styling */
div[data-testid="stCheckbox"] label span p {
    font-size: 0.8rem !important;
    color: #374151 !important;
}
</style>
"""
    md_html(styles_html)


def render_login_page(auth_service: AuthService) -> None:
    """Render Login Page matching Target Specification (Email/Password Only, No Social Login)."""
    inject_auth_styles()

    col_left, col_right = st.columns([0.29, 0.71], gap="small")

    with col_left:
        render_left_panel()

    with col_right:
        header_html = """\
<div style="width: 100%; max-width: 420px; margin: 0 auto;">
<h1 style="font-family: Georgia, serif; font-size: 2.0rem; font-weight: 700; color: #1B4332; margin-bottom: 0.2rem; text-align: center;">Welcome Back</h1>
<p style="font-size: 0.86rem; color: #53645f; margin-bottom: 1.25rem; text-align: center;">Login to your IP-SAKTI account</p>
</div>
"""
        md_html(header_html)

        with st.form("login_form", clear_on_submit=False):
            st.text_input("Email", placeholder="✉  Enter your email", key="login_email_input")

            # Password Label + Forgot Password link on exact same horizontal row
            pw_label_html = """\
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; margin-top: 0.65rem;">
<label style="font-size: 0.84rem; font-weight: 600; color: #374151; margin: 0;">Password</label>
<a href="#" style="font-size: 0.78rem; color: #1B4332; font-weight: 600; text-decoration: none;">Forgot password?</a>
</div>
"""
            md_html(pw_label_html)

            st.text_input("Password", type="password", placeholder="🔒  Enter your password", label_visibility="collapsed", key="login_password_input")

            md_html('<div style="height: 0.85rem;"></div>')
            submitted = st.form_submit_button("Login →", use_container_width=True)

            if submitted:
                email_val = st.session_state.get("login_email_input", "")
                pwd_val = st.session_state.get("login_password_input", "")
                user_data, error = auth_service.authenticate_user(email=email_val, password=pwd_val)
                if error:
                    st.error(error)
                else:
                    # Create persistent browser session
                    session_mgr = get_session_manager()
                    signed_token = session_mgr.create_session(user_data["id"])
                    try:
                        st.query_params["session"] = signed_token
                    except Exception as q_err:
                        logger.warning(f"Could not set query params session: {q_err}")
                    cookie_manager = _get_cookie_manager()
                    if cookie_manager is not None:
                        try:
                            cookie_manager.set(
                                COOKIE_NAME,
                                signed_token,
                                key="login_cookie_set",
                                max_age=30 * 24 * 3600,  # 30 days in seconds
                            )
                        except Exception as e:
                            logger.warning(f"Could not set login cookie: {e}")
                    st.session_state.authenticated_user = user_data
                    st.session_state["session_token"] = signed_token
                    st.session_state["page"] = "dashboard"
                    st.session_state.auth_page = "authenticated"
                    st.session_state.active_conversation_id = None
                    st.session_state.messages = []
                    st.rerun()

        footer_html = """\
<div style="width: 100%; max-width: 420px; margin: 1.5rem auto 0 auto; text-align: center; font-size: 0.86rem; color: #374151;">
Don't have an account?
</div>
"""
        md_html(footer_html)
        if st.button("Register here", key="btn_goto_register", use_container_width=True):
            st.session_state["page"] = "register"
            st.session_state.auth_page = "register"
            st.rerun()


def render_registration_page(auth_service: AuthService) -> None:
    """Render Registration Page matching Target Specification (Email/Password Only, No Social Login)."""
    inject_auth_styles()

    col_left, col_right = st.columns([0.29, 0.71], gap="small")

    with col_left:
        render_left_panel()

    with col_right:
        header_html = """\
<div style="width: 100%; max-width: 500px; margin: 0 auto;">
<h1 style="font-family: Georgia, serif; font-size: 1.9rem; font-weight: 700; color: #1B4332; margin-bottom: 0.2rem; text-align: center;">Create Your Account</h1>
<p style="font-size: 0.86rem; color: #53645f; margin-bottom: 1.15rem; text-align: center;">Join IP-SAKTI and start your research journey</p>
</div>
"""
        md_html(header_html)

        with st.form("reg_form", clear_on_submit=False):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.text_input("Full Name", placeholder="👤  Enter your full name", key="reg_name_input")
            with f_col2:
                st.text_input("Email", placeholder="✉  Enter your email", key="reg_email_input")

            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.text_input("Password", type="password", placeholder="🔒  Create a password", key="reg_pwd_input")
            with p_col2:
                st.text_input("Confirm Password", type="password", placeholder="🔒  Confirm your password", key="reg_confirm_pwd_input")

            md_html('<div style="height: 0.15rem;"></div>')
            terms = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="reg_terms_input")

            md_html('<div style="height: 0.65rem;"></div>')
            submitted = st.form_submit_button("Register →", use_container_width=True)

            if submitted:
                name_val = st.session_state.get("reg_name_input", "")
                email_val = st.session_state.get("reg_email_input", "")
                pwd_val = st.session_state.get("reg_pwd_input", "")
                confirm_val = st.session_state.get("reg_confirm_pwd_input", "")
                user_data, error = auth_service.register_user(
                    name=name_val,
                    email=email_val,
                    password=pwd_val,
                    confirm_password=confirm_val,
                    terms_accepted=terms,
                )
                if error:
                    st.error(error)
                else:
                    st.success("Registration successful! Logging you in...")
                    # Create persistent browser session
                    session_mgr = get_session_manager()
                    signed_token = session_mgr.create_session(user_data["id"])
                    try:
                        st.query_params["session"] = signed_token
                    except Exception as q_err:
                        logger.warning(f"Could not set query params session: {q_err}")
                    cookie_manager = _get_cookie_manager()
                    if cookie_manager is not None:
                        try:
                            cookie_manager.set(
                                COOKIE_NAME,
                                signed_token,
                                key="reg_cookie_set",
                                max_age=30 * 24 * 3600,  # 30 days in seconds
                            )
                        except Exception as e:
                            logger.warning(f"Could not set registration cookie: {e}")
                    st.session_state.authenticated_user = user_data
                    st.session_state["session_token"] = signed_token
                    st.session_state["page"] = "dashboard"
                    st.session_state.auth_page = "authenticated"
                    st.session_state.active_conversation_id = None
                    st.session_state.messages = []
                    st.rerun()

        footer_html = """\
<div style="width: 100%; max-width: 500px; margin: 1.35rem auto 0 auto; text-align: center; font-size: 0.86rem; color: #374151;">
Already have an account?
</div>
"""
        md_html(footer_html)
        if st.button("Login here", key="btn_goto_login", use_container_width=True):
            st.session_state["page"] = "login"
            st.session_state.auth_page = "login"
            st.rerun()


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

def render_landing_page() -> None:
    """Render initial research interface matching reference screenshot EXACTLY."""

    # 1. Botanical Background Layers
    botanical_html = """\
<div class="botanical-bg-container">
  <!-- Top Left Botanical Branch -->
  <svg class="botanical-leaf bot-top-left" width="360" height="360" viewBox="0 0 360 360" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M-30 -30 Q 70 80, 200 210 T 340 340" stroke="#1D4A32" stroke-width="3.5" stroke-linecap="round"/>
    <path d="M30 25 C 0 -15, 75 -25, 115 15 C 85 45, 40 50, 30 25 Z" fill="#2E6446" opacity="0.88"/>
    <path d="M30 25 Q 75 0 115 15" stroke="#123A24" stroke-width="1.2"/>
    <path d="M70 65 C 30 20, 120 5, 160 55 C 120 90, 75 90, 70 65 Z" fill="#3B7754" opacity="0.92"/>
    <path d="M70 65 Q 115 35 160 55" stroke="#123A24" stroke-width="1.2"/>
    <path d="M115 115 C 60 65, 170 45, 210 100 C 160 140, 120 145, 115 115 Z" fill="#245439" opacity="0.85"/>
    <path d="M115 115 Q 165 80 210 100" stroke="#123A24" stroke-width="1.2"/>
    <path d="M165 170 C 115 120, 230 95, 275 155 C 220 195, 175 195, 165 170 Z" fill="#34704E" opacity="0.9"/>
    <path d="M165 170 Q 220 135 275 155" stroke="#123A24" stroke-width="1.2"/>
    <path d="M15 55 C -25 75, -10 145, 40 130 C 50 95, 35 65, 15 55 Z" fill="#44845E" opacity="0.88"/>
    <path d="M55 105 C 15 125, 25 195, 75 180 C 85 145, 70 115, 55 105 Z" fill="#2D6345" opacity="0.91"/>
  </svg>

  <!-- Top Right Botanical Branch -->
  <svg class="botanical-leaf bot-top-right" width="400" height="400" viewBox="0 0 400 400" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M430 -30 Q 310 90, 180 210 T 20 380" stroke="#1B462E" stroke-width="4" stroke-linecap="round"/>
    <path d="M340 30 C 380 -15, 295 -25, 255 15 C 285 50, 330 55, 340 30 Z" fill="#2E6446" opacity="0.9"/>
    <path d="M340 30 Q 295 0 255 15" stroke="#123A24" stroke-width="1.2"/>
    <path d="M295 75 C 335 30, 245 15, 205 60 C 235 95, 285 95, 295 75 Z" fill="#3A7553" opacity="0.88"/>
    <path d="M295 75 Q 250 40 205 60" stroke="#123A24" stroke-width="1.2"/>
    <path d="M245 130 C 290 80, 190 60, 145 110 C 185 150, 235 150, 245 130 Z" fill="#225338" opacity="0.92"/>
    <path d="M245 130 Q 195 95 145 110" stroke="#123A24" stroke-width="1.2"/>
    <path d="M195 190 C 240 140, 135 115, 90 170 C 135 210, 185 210, 195 190 Z" fill="#35714F" opacity="0.87"/>
    <path d="M195 190 Q 140 150 90 170" stroke="#123A24" stroke-width="1.2"/>
    <path d="M360 65 C 400 85, 385 155, 335 140 C 320 105, 340 75, 360 65 Z" fill="#295D40" opacity="0.89"/>
  </svg>

  <!-- Bottom Left Botanical Branch -->
  <svg class="botanical-leaf bot-bottom-left" width="380" height="380" viewBox="0 0 380 380" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M-30 410 Q 90 290, 200 170 T 360 10" stroke="#1B462E" stroke-width="3.5" stroke-linecap="round"/>
    <path d="M35 335 C -5 375, 70 395, 105 350 C 80 320, 40 315, 35 335 Z" fill="#2A5F42" opacity="0.9"/>
    <path d="M80 290 C 40 330, 125 350, 160 300 C 130 270, 85 270, 80 290 Z" fill="#3B7754" opacity="0.88"/>
    <path d="M130 235 C 85 280, 180 300, 215 250 C 180 215, 135 215, 130 235 Z" fill="#215136" opacity="0.92"/>
  </svg>

  <!-- Bottom Right Botanical Branch -->
  <svg class="botanical-leaf bot-bottom-right" width="440" height="440" viewBox="0 0 440 440" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M470 470 Q 320 340, 190 200 T 20 20" stroke="#1A452D" stroke-width="4" stroke-linecap="round"/>
    <path d="M380 380 C 420 340, 340 320, 305 365 C 330 395, 370 400, 380 380 Z" fill="#2E6446" opacity="0.91"/>
    <path d="M330 325 C 370 285, 285 265, 250 310 C 280 340, 320 345, 330 325 Z" fill="#3B7754" opacity="0.87"/>
    <path d="M275 265 C 320 220, 225 205, 190 255 C 225 290, 265 290, 275 265 Z" fill="#225338" opacity="0.92"/>
  </svg>

  <!-- Floating Leaf -->
  <svg class="botanical-leaf bot-float-1" width="140" height="140" viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 30 C 45 10, 80 25, 65 65 C 45 80, 10 55, 20 30 Z" fill="#2E6446" opacity="0.6"/>
    <path d="M20 30 Q 48 45 65 65" stroke="#1B462E" stroke-width="1" fill="none" opacity="0.65"/>
  </svg>
</div>
"""
    md_html(botanical_html)

    # 2. Hero Section
    md_html('<div class="hero-tagline">Sahayak, sahayak — "the one who assists"</div>')
    md_html('<div class="hero-heading">Ask before you file.</div>')
    md_html(
        '<div class="hero-subtext">'
        'Decision-support research for Traditional Knowledge, patent prior art, AYUSH regulatory compliance, and '
        'Access & Benefit Sharing — grounded in available source texts.'
        '</div>'
    )

    # 3. Three Feature Cards (Horizontal Row)
    col1, col2, col3 = st.columns(3)

    with col1:
        md_html(
            """\
            <div class="feature-card">
              <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.5rem;">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#003E29" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <circle cx="11.5" cy="14.5" r="2.5"></circle>
                  <path d="M13.5 16.5L16 19"></path>
                </svg>
                <div class="feature-card-title" style="margin: 0;">Prior Art Inquiry</div>
              </div>
              <div class="feature-card-copy">
                Explore patent prior art, exclusions and Traditional Knowledge references.
              </div>
            </div>
            """
        )
        if st.button("Prior Art Inquiry →", key="btn_card_prior_art", use_container_width=True):
            st.session_state.pending_query = "Is turmeric + neem patentable in India?"
            st.rerun()

    with col2:
        md_html(
            """\
            <div class="feature-card">
              <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.5rem;">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#003E29" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"></path>
                  <path d="M12 6v6l4 2"></path>
                </svg>
                <div class="feature-card-title" style="margin: 0;">AYUSH Compliance</div>
              </div>
              <div class="feature-card-copy">
                Examine regulatory requirements and formulation-specific considerations.
              </div>
            </div>
            """
        )
        if st.button("AYUSH Compliance →", key="btn_card_ayush", use_container_width=True):
            st.session_state.pending_query = "AYUSH licensing steps under Rule 158-B"
            st.rerun()

    with col3:
        md_html(
            """\
            <div class="feature-card">
              <div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 0.5rem;">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#003E29" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path>
                  <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path>
                </svg>
                <div class="feature-card-title" style="margin: 0;">ABS & Consent</div>
              </div>
              <div class="feature-card-copy">
                Examine Access & Benefit-Sharing obligations and relevant biological-resource provisions.
              </div>
            </div>
            """
        )
        if st.button("ABS & Consent →", key="btn_card_abs", use_container_width=True):
            st.session_state.pending_query = "ABS obligations under Biodiversity Act"
            st.rerun()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Streamlit application."""

    inject_styles()

    chat_storage = get_chat_storage()
    auth_service = get_auth_service()

    # Session State initialisation
    if "authenticated_user" not in st.session_state:
        st.session_state.authenticated_user = None

    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    if "auth_page" not in st.session_state:
        st.session_state.auth_page = st.session_state["page"]

    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False

    # Restore auth from persistent browser cookie on every rerun
    # (handles browser refresh — must run before the unauthenticated gate)
    initialize_authentication()

    # 1. Unauthenticated views

    if st.session_state.authenticated_user is None:
        current_page = st.session_state.get("page", st.session_state.get("auth_page", "login"))
        if current_page == "register":
            render_registration_page(auth_service)
        else:
            render_login_page(auth_service)
        return

    # 2. Authenticated Application
    user = st.session_state.authenticated_user
    user_id = user["id"]

    # Ensure session token is synchronized to browser URL query parameters during page rendering
    if "session_token" in st.session_state and st.session_state["session_token"]:
        token_val = str(st.session_state["session_token"])
        if st.query_params.get("session") != token_val:
            try:
                st.query_params["session"] = token_val
            except Exception as sync_err:
                logger.warning(f"Could not sync query param session: {sync_err}")

    # Render header user profile control
    render_header_user_profile(user)

    # Render Settings view if active
    if st.session_state.show_settings:
        render_settings_view(user)
        return

    # Ensure active conversation session is initialised for active user
    if "active_conversation_id" not in st.session_state or not st.session_state.active_conversation_id:
        existing = chat_storage.list_conversations(user_id=user_id, limit=1)
        if existing:
            st.session_state.active_conversation_id = existing[0]["id"]
            conv_data = chat_storage.get_conversation(existing[0]["id"], user_id=user_id)
            if conv_data and "messages" in conv_data:
                restored = []
                for m in conv_data["messages"]:
                    role = m["role"]
                    content = m["content"]
                    meta = m.get("metadata")
                    if role == "assistant" and meta and isinstance(meta, dict):
                        restored.append({"role": role, "content": meta})
                    elif role == "assistant" and isinstance(content, str) and content.startswith("{"):
                        try:
                            restored.append({"role": role, "content": json.loads(content)})
                        except Exception:
                            restored.append({"role": role, "content": content})
                    else:
                        restored.append({"role": role, "content": content})
                st.session_state.messages = restored
            else:
                st.session_state.messages = []
        else:
            new_conv = chat_storage.create_conversation("New Chat", user_id=user_id)
            st.session_state.active_conversation_id = new_conv["id"]
            st.session_state.messages = []

    filters = render_sidebar(chat_storage, user_id=user_id)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None

    # Initial landing page
    if not st.session_state.messages:
        render_landing_page()

    # Existing conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                render_user_message(message["content"])
            else:
                render_response(message["content"], filters)

    # -------------------------------------------------------------------
    # Suggested query submitted
    # -------------------------------------------------------------------
    pending_query = st.session_state.pending_query

    if pending_query:
        st.session_state.pending_query = None
        active_cid = st.session_state.active_conversation_id

        # Format bounded context history (up to last 4 messages)
        history_turns = []
        for m in st.session_state.messages[-4:]:
            r_role = m["role"]
            r_content = m["content"]
            text_str = r_content.get("answer", "") if isinstance(r_content, dict) else str(r_content)
            if text_str.strip():
                history_turns.append({"role": r_role, "content": text_str})

        st.session_state.messages.append({"role": "user", "content": pending_query})

        with st.chat_message("user"):
            render_user_message(pending_query)

        with st.chat_message("assistant"):
            with st.spinner("Researching available evidence…"):
                try:
                    result = query_backend_api(
                        raw_query=pending_query,
                        jurisdiction=filters["jurisdiction"],
                        formulation_category=filters["formulation"],
                        user_language=filters["user_lang"],
                        api_base_url=filters["api_url"],
                        conversation_id=active_cid,
                        conversation_history=history_turns,
                    )
                    st.session_state.messages.append({"role": "assistant", "content": result})
                    chat_storage.add_message(active_cid, "user", pending_query, user_id=user_id)
                    chat_storage.add_message(active_cid, "assistant", result, user_id=user_id)
                    render_response(result, filters)
                except Exception as exc:
                    st.error(f"Something went wrong while processing the request: {exc}")

    # -------------------------------------------------------------------
    # Normal chat input
    # -------------------------------------------------------------------
    prompt = st.chat_input("Ask about Traditional Knowledge, patents, AYUSH or ABS…")

    if prompt:
        prompt = prompt.strip()
        if not prompt:
            return

        active_cid = st.session_state.active_conversation_id

        # Format bounded context history (up to last 4 messages)
        history_turns = []
        for m in st.session_state.messages[-4:]:
            r_role = m["role"]
            r_content = m["content"]
            text_str = r_content.get("answer", "") if isinstance(r_content, dict) else str(r_content)
            if text_str.strip():
                history_turns.append({"role": r_role, "content": text_str})

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            render_user_message(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Researching available evidence…"):
                try:
                    result = query_backend_api(
                        raw_query=prompt,
                        jurisdiction=filters["jurisdiction"],
                        formulation_category=filters["formulation"],
                        user_language=filters["user_lang"],
                        api_base_url=filters["api_url"],
                        conversation_id=active_cid,
                        conversation_history=history_turns,
                    )
                    st.session_state.messages.append({"role": "assistant", "content": result})
                    chat_storage.add_message(active_cid, "user", prompt, user_id=user_id)
                    chat_storage.add_message(active_cid, "assistant", result, user_id=user_id)
                    render_response(result, filters)
                except Exception as exc:
                    st.error(f"Something went wrong while processing the request: {exc}")



if __name__ == "__main__":
    main()