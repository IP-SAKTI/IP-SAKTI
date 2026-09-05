"""
ip_sakti.ui.app — Streamlit Web Interface for IP-SAKTI Sahayak.

Editorial-style multilingual interface for Traditional Knowledge,
Intellectual Property, AYUSH and Access & Benefit-Sharing research.

The UI communicates with the existing FastAPI backend. No retrieval,
orchestration, LLM, or database logic is implemented here.
"""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import streamlit as st


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
    """Apply the visual system for the IP-SAKTI interface."""

    st.markdown(
        """
        <style>

        /* ---------------------------------------------------------------
           Global palette
        --------------------------------------------------------------- */

        :root {
            --parchment: #f4efdf;
            --parchment-soft: #faf7ed;
            --ink: #173f35;
            --ink-soft: #53645f;
            --navy: #192b4a;
            --navy-deep: #14233e;
            --green: #527d62;
            --green-soft: #dce7dc;
            --turmeric: #c99738;
            --line: #d8d0bd;
            --white: #fffdf7;
        }

        /* Main application */
        .stApp {
            background: var(--parchment);
            color: var(--ink);
        }

        .main .block-container {
            max-width: 1280px;
            padding-top: 3.5rem;
            padding-bottom: 6rem;
        }

        /* Remove Streamlit's default top chrome */
        header[data-testid="stHeader"] {
            background: var(--parchment);
            height: 0;
        }

        header[data-testid="stHeader"] > div {
            display: none;
        }

        /* Remove bottom decoration */
        footer {
            visibility: hidden;
        }

        /* ---------------------------------------------------------------
           Sidebar
        --------------------------------------------------------------- */

        section[data-testid="stSidebar"] {
            background: var(--navy);
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        section[data-testid="stSidebar"] > div {
            background: var(--navy);
            padding: 1.8rem 1.55rem;
        }

        section[data-testid="stSidebar"] * {
            color: #f4f0e5;
        }

        section[data-testid="stSidebar"] hr {
            border: none;
            border-top: 1px solid rgba(255,255,255,0.15);
            margin: 1.45rem 0;
        }

        .sidebar-logo, [data-testid="stSidebar"] [data-testid="stImage"] {
            display: flex;
            justify-content: center;
            align-items: center;
            background: transparent !important;
            margin: 0.2rem auto 0.4rem auto;
            text-align: center;
        }

        .sidebar-logo img, [data-testid="stSidebar"] [data-testid="stImage"] img {
            width: 85px !important;
            max-width: 85px !important;
            height: auto !important;
            background: transparent !important;
            margin: 0 auto !important;
        }

        .sidebar-brand {
            text-align: center;
            margin-bottom: 1.35rem;
        }

        .sidebar-brand-name {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.12rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }

        .sidebar-brand-subtitle {
            margin-top: 0.2rem;
            margin-bottom: 0.8rem;
            text-align: center;
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.76rem;
            color: rgba(244,240,229,0.68) !important;
        }

        .sidebar-section-title {
            margin-bottom: 0.85rem;
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(244,240,229,0.62) !important;
        }

        .sidebar-version {
            text-align: center;
            margin-top: 2rem;
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.7rem;
            color: rgba(244,240,229,0.48) !important;
        }

        /* Sidebar select boxes */
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: rgba(10,17,29,0.82);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 8px;
            min-height: 44px;
        }

        section[data-testid="stSidebar"] label {
            font-size: 0.82rem;
            font-weight: 600;
        }

        /* ---------------------------------------------------------------
           Typography
        --------------------------------------------------------------- */

        .eyebrow {
            font-family: Georgia, "Times New Roman", serif;
            font-style: italic;
            font-size: 1rem;
            color: var(--green);
            margin-bottom: 0.65rem;
        }

        .hero-title {
            margin: 0;
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(2.4rem, 4vw, 4rem);
            line-height: 1.04;
            font-weight: 500;
            letter-spacing: -0.035em;
            color: var(--ink);
        }

        .hero-description {
            max-width: 850px;
            margin-top: 1rem;
            margin-bottom: 2rem;
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 1rem;
            line-height: 1.7;
            color: var(--ink-soft);
        }

        /* ---------------------------------------------------------------
           Research directions
        --------------------------------------------------------------- */

        .research-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            margin: 1.5rem 0 1.9rem 0;
        }

        .research-item {
            padding: 0.35rem 1rem 0.35rem 1.1rem;
            border-left: 2px solid var(--green);
        }

        .research-title {
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 0.55rem;
        }

        .research-copy {
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.8rem;
            line-height: 1.65;
            color: var(--ink-soft);
        }

        /* ---------------------------------------------------------------
           Suggested queries
        --------------------------------------------------------------- */

        .suggested-label {
            margin-top: 1.2rem;
            margin-bottom: 0.55rem;
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.76rem;
            font-weight: 700;
            color: var(--green);
        }

        div[data-testid="stHorizontalBlock"] button,
        .stButton button,
        .suggested-query button {
            background: #e8e1cf !important;
            border: 1px solid #d4cca9 !important;
            color: #173f35 !important;
            font-family: "IBM Plex Sans", Arial, sans-serif !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            text-align: left !important;
            min-height: 50px !important;
            padding: 0.65rem 0.85rem !important;
            border-radius: 6px !important;
            box-shadow: none !important;
        }

        div[data-testid="stHorizontalBlock"] button:hover,
        .stButton button:hover,
        .suggested-query button:hover {
            border-color: #527d62 !important;
            color: #173f35 !important;
            background: #ded6bf !important;
        }

        /* ---------------------------------------------------------------
           Conversation & Chat Avatars
        --------------------------------------------------------------- */

        /* Hide default Streamlit chat avatars completely */
        [data-testid="stChatMessageAvatarUser"],
        [data-testid="stChatMessageAvatarAssistant"],
        [data-testid="stChatMessageAvatarSystem"],
        [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"],
        .stChatMessage [data-testid="stChatMessageAvatar"] {
            display: none !important;
        }

        /* Clean Streamlit chat message containers */
        [data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin-bottom: 1.5rem !important;
        }

        [data-testid="stChatMessageContent"] {
            padding: 0 !important;
            width: 100% !important;
        }

        /* ---------------------------------------------------------------
           User message block
        --------------------------------------------------------------- */

        .user-message-wrapper {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            margin: 0.6rem 0 1.4rem auto;
            max-width: 80%;
        }

        .user-message-author {
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--green);
            margin-bottom: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            text-align: right;
        }

        .user-message-body {
            background: #faf7ed;
            border: 1px solid #d8d0bd;
            border-radius: 8px;
            padding: 0.85rem 1.15rem;
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.96rem;
            line-height: 1.6;
            color: #173f35 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            word-break: break-word;
        }

        .user-message-body p {
            color: #173f35 !important;
            margin: 0;
        }

        /* ---------------------------------------------------------------
           Response area & Metadata
        --------------------------------------------------------------- */

        .response-label {
            margin-top: 0.4rem;
            margin-bottom: 0.65rem;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--ink);
            letter-spacing: -0.01em;
        }

        .response-text {
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.96rem;
            line-height: 1.75;
            color: #263a35;
            margin-bottom: 1.4rem;
        }

        .status-line {
            display: flex;
            align-items: center;
            gap: 1.2rem;
            flex-wrap: wrap;
            margin: 0.4rem 0 1.2rem 0;
            padding-bottom: 0.85rem;
            border-bottom: 1px solid var(--line);
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.78rem;
            color: var(--ink-soft);
        }

        .status-label {
            font-weight: 600;
            color: var(--ink);
        }

        .status-sep {
            color: var(--line);
            font-size: 0.72rem;
        }

        .evidence-card {
            margin: 0.8rem 0;
            padding: 0.95rem 1.15rem;
            border: 1px solid var(--line);
            border-radius: 6px;
            background: #faf7ed;
        }

        .evidence-title {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 0.98rem;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 0.25rem;
        }

        .evidence-meta {
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.74rem;
            color: var(--ink-soft);
            margin-bottom: 0.65rem;
        }

        .evidence-content {
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.84rem;
            line-height: 1.65;
            color: #394b46;
        }

        /* ---------------------------------------------------------------
           Abstention
        --------------------------------------------------------------- */

        .facilitator-box {
            margin: 1.2rem 0 1.5rem 0;
            padding: 1.1rem 1.3rem;
            border-left: 3px solid var(--turmeric);
            background: #faf7ed;
            border-top: 1px solid rgba(201,151,56,0.18);
            border-right: 1px solid rgba(201,151,56,0.18);
            border-bottom: 1px solid rgba(201,151,56,0.18);
            border-radius: 0 6px 6px 0;
        }

        .facilitator-title {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 0.35rem;
        }

        .facilitator-copy {
            font-family: "IBM Plex Sans", Arial, sans-serif;
            font-size: 0.84rem;
            line-height: 1.65;
            color: var(--ink-soft);
        }

        /* ---------------------------------------------------------------
           Metrics & Expanders
        --------------------------------------------------------------- */

        div[data-testid="stExpander"] {
            border: 1px solid var(--line) !important;
            border-radius: 6px !important;
            background: #faf7ed !important;
            margin-top: 1rem !important;
            margin-bottom: 1rem !important;
            box-shadow: none !important;
        }

        div[data-testid="stExpander"] summary {
            font-family: "IBM Plex Sans", Arial, sans-serif !important;
            font-size: 0.84rem !important;
            font-weight: 600 !important;
            color: var(--ink) !important;
        }

        div[data-testid="stMetric"] {
            background: transparent !important;
            padding: 0.2rem 0 !important;
        }

        div[data-testid="stMetricLabel"] {
            font-family: "IBM Plex Sans", Arial, sans-serif !important;
            font-size: 0.74rem !important;
            color: var(--ink-soft) !important;
            font-weight: 500 !important;
        }

        div[data-testid="stMetricValue"] {
            font-family: Georgia, "Times New Roman", serif !important;
            font-size: 1.3rem !important;
            color: var(--ink) !important;
            font-weight: 600 !important;
        }

        /* ---------------------------------------------------------------
           Chat input & Bottom area styling
        --------------------------------------------------------------- */

        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        div[data-testid="stBottom"],
        div[data-testid="stChatInput"] {
            background-color: var(--parchment) !important;
            background: var(--parchment) !important;
            border-top: none !important;
        }

        div[data-testid="stChatInput"] {
            padding: 0.5rem 0 1rem 0 !important;
        }

        div[data-testid="stChatInput"] > div {
            background-color: var(--white) !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
        }

        div[data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: var(--ink) !important;
            border: none !important;
            font-family: "IBM Plex Sans", Arial, sans-serif !important;
            font-size: 0.9rem !important;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #7c817a !important;
        }

        div[data-testid="stChatInput"] button {
            background: var(--ink) !important;
            color: var(--white) !important;
            border-radius: 6px !important;
            border: none !important;
        }


        /* Disclaimer styling */
        .disclaimer-text,
        [data-testid="stCaptionContainer"],
        .stCaption,
        div[data-testid="stCaptionContainer"] p {
            color: #53645f !important;
            font-family: "IBM Plex Sans", Arial, sans-serif !important;
            font-size: 0.76rem !important;
            font-weight: 400 !important;
            line-height: 1.6 !important;
            margin-top: 1.2rem !important;
            margin-bottom: 0.8rem !important;
        }

        /* Responsive layout */
        @media (max-width: 900px) {
            .research-grid {
                grid-template-columns: 1fr;
                gap: 1.25rem;
            }

            .hero-title {
                font-size: 2.5rem;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
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
) -> Dict[str, Any]:
    """
    Send the user request to the existing FastAPI /query endpoint.

    The UI does not perform retrieval, orchestration, synthesis,
    confidence assessment, or citation generation itself.
    """

    url = f"{api_base_url.rstrip('/')}/query"

    payload = {
        "raw_query": raw_query,
        "jurisdiction": jurisdiction,
        "formulation_category": formulation_category,
        "user_language": (
            user_language if user_language != "auto" else None
        ),
    }

    response = httpx.post(
        url,
        json=payload,
        timeout=60.0,
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> Dict[str, Any]:
    """Render the application controls."""

    if LOGO_PATH.exists():
        st.sidebar.image(
            str(LOGO_PATH),
            width=85,
        )
        st.sidebar.markdown(
            '<div class="sidebar-brand-subtitle">'
            'Traditional Knowledge · IP · AYUSH'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-name">
                    IP-SAKTI Sahayak
                </div>
                <div class="sidebar-brand-subtitle">
                    Traditional Knowledge · IP · AYUSH
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        '<div class="sidebar-section-title">Jurisdiction & Scope</div>',
        unsafe_allow_html=True,
    )

    jurisdiction_options = {
        "Auto-detect": "unknown",
        "India": "india",
        "International": "international",
        "Both (India & Int'l)": "both",
    }

    selected_j_label = st.sidebar.selectbox(
        "Target Jurisdiction",
        options=list(jurisdiction_options.keys()),
        index=0,
    )

    jurisdiction = jurisdiction_options[selected_j_label]

    formulation_options = {
        "Auto-detect": "unknown",
        "Classical Ayurvedic": "classical",
        "Proprietary Medicine": "proprietary",
        "New Drug": "new_drug",
        "Phytopharmaceutical": "phytopharmaceutical",
        "Nutraceutical": "nutraceutical",
        "Cosmetic": "cosmetic",
    }

    selected_f_label = st.sidebar.selectbox(
        "Formulation Category",
        options=list(formulation_options.keys()),
        index=0,
    )

    formulation = formulation_options[selected_f_label]

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        '<div class="sidebar-section-title">Language</div>',
        unsafe_allow_html=True,
    )

    language_options = {
        "Auto-detect": "auto",
        "English (en)": "en",
        "Hindi (hi)": "hi",
        "Tamil (ta)": "ta",
        "Telugu (te)": "te",
        "Kannada (kn)": "kn",
        "Marathi (mr)": "mr",
        "Bengali (bn)": "bn",
        "Gujarati (gu)": "gu",
        "Malayalam (ml)": "ml",
        "Punjabi (pa)": "pa",
        "Odia (or)": "or",
    }

    selected_lang_label = st.sidebar.selectbox(
        "Query / Response Language",
        options=list(language_options.keys()),
        index=0,
    )

    user_lang = language_options[selected_lang_label]

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        f"""
        <div class="sidebar-version">
            IP-SAKTI Sahayak {APP_VERSION}
        </div>
        """,
        unsafe_allow_html=True,
    )

    return {
        "jurisdiction": jurisdiction,
        "formulation": formulation,
        "user_lang": user_lang,
        "api_url": DEFAULT_API_BASE_URL,
    }


# ---------------------------------------------------------------------------
# Message rendering
# ---------------------------------------------------------------------------

def render_user_message(text: str) -> None:
    """Render a clean, editorial user query block."""

    escaped_text = html.escape(text)
    st.markdown(
        f"""
        <div class="user-message-wrapper">
            <div class="user-message-author">You</div>
            <div class="user-message-body">{escaped_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_response(res: Dict[str, Any]) -> None:
    """Render an actual backend response."""

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

    if confidence and "score" in confidence:
        confidence_text = f"{confidence['score'] * 100:.0f}%"
    else:
        confidence_text = "—"

    status_text = (
        "Safe abstention"
        if is_abstention
        else "Source-grounded response"
    )

    st.markdown(
        f"""
        <div class="status-line">
            <span><strong class="status-label">Status</strong> · {status_text}</span>
            <span class="status-sep">|</span>
            <span><strong class="status-label">Confidence</strong> · {confidence_text}</span>
            <span class="status-sep">|</span>
            <span><strong class="status-label">Agents</strong> · {agent_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------
    # Answer
    # ---------------------------------------------------------------

    if is_abstention:
        st.markdown(
            '<div class="response-label">Unable to provide a reliable conclusion</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="response-text">{answer}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
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
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            '<div class="response-label">Response</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="response-text">{answer}</div>',
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------------
    # Confidence details
    # ---------------------------------------------------------------

    if confidence:
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

    if evidence:
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

                url = chunk.get("source_url")

                st.markdown(
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
                    """,
                    unsafe_allow_html=True,
                )

                if url:
                    st.markdown(
                        f"[View source document]({url})"
                    )

    # ---------------------------------------------------------------
    # Disclaimer
    # ---------------------------------------------------------------

    if disclaimer:
        st.markdown(
            f'<div class="disclaimer-text">{disclaimer}</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

def render_landing_page() -> None:
    """Render the initial research interface."""

    st.markdown(
        '<div class="eyebrow">Sahayak, sahaayak — "the one who assists"</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-title">Ask before you file.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-description">Decision-support research for Traditional Knowledge, patent prior art, AYUSH regulatory compliance, and Access & Benefit Sharing — grounded in available source texts.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="research-item">'
            '<div class="research-title">Prior Art Inquiry</div>'
            '<div class="research-copy">Explore patent prior art, exclusions and Traditional Knowledge references.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="research-item">'
            '<div class="research-title">AYUSH Compliance</div>'
            '<div class="research-copy">Examine regulatory requirements and formulation-specific considerations.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="research-item">'
            '<div class="research-title">ABS & Consent</div>'
            '<div class="research-copy">Examine Access & Benefit-Sharing obligations and relevant biological-resource provisions.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="suggested-label">Suggested research queries</div>',
        unsafe_allow_html=True,
    )

    queries = [
        "Is turmeric + neem patentable in India?  →",
        "AYUSH licensing steps under Rule 158-B  →",
        "ABS obligations under Biodiversity Act  →",
    ]

    cols = st.columns(3)

    for index, query in enumerate(queries):

        with cols[index]:

            st.markdown(
                '<div class="suggested-query">',
                unsafe_allow_html=True,
            )

            if st.button(
                query,
                key=f"suggested_query_{index}",
                use_container_width=True,
            ):
                st.session_state.pending_query = query.replace("  →", "").strip()

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

    st.markdown(
        "<hr style='border:none;border-top:1px solid #d8d0bd;margin-top:2rem;'>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Streamlit application."""

    inject_styles()

    filters = render_sidebar()

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
                render_response(message["content"])

    # -------------------------------------------------------------------
    # Suggested query submitted
    # -------------------------------------------------------------------

    pending_query = st.session_state.pending_query

    if pending_query:

        st.session_state.pending_query = None

        st.session_state.messages.append(
            {
                "role": "user",
                "content": pending_query,
            }
        )

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
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": result,
                        }
                    )

                    render_response(result)

                except httpx.HTTPStatusError as exc:

                    st.error(
                        "The request could not be completed."
                    )

                    if exc.response is not None:
                        st.caption(
                            f"Backend returned HTTP {exc.response.status_code}."
                        )

                except httpx.RequestError:

                    st.error(
                        "The request could not be completed right now."
                    )

                except Exception:

                    st.error(
                        "Something went wrong while processing the request."
                    )

    # -------------------------------------------------------------------
    # Normal chat input
    # -------------------------------------------------------------------

    prompt = st.chat_input(
        "Ask about Traditional Knowledge, patents, AYUSH or ABS…"
    )

    if prompt:

        prompt = prompt.strip()

        if not prompt:
            return

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

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
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": result,
                        }
                    )

                    render_response(result)

                except httpx.HTTPStatusError as exc:

                    st.error(
                        "The request could not be completed."
                    )

                    if exc.response is not None:
                        st.caption(
                            f"Backend returned HTTP {exc.response.status_code}."
                        )

                except httpx.RequestError:

                    st.error(
                        "The request could not be completed right now."
                    )

                except Exception:

                    st.error(
                        "Something went wrong while processing the request."
                    )


if __name__ == "__main__":
    main()