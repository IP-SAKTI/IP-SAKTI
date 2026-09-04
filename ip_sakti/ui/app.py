"""
ip_sakti.ui.app — Streamlit Web Interface for IP-SAKTI Sahayak.

Provides a modern, responsive multilingual chat and decision-support interface.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

import httpx
import streamlit as st

# Custom page configuration
st.set_page_config(
    page_title="IP-SAKTI Sahayak — Traditional Knowledge & IP Assistant",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configuration from environment
DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def query_backend_api(
    raw_query: str,
    jurisdiction: str,
    formulation_category: str,
    user_language: Optional[str],
    api_base_url: str,
) -> Dict[str, Any]:
    """
    Send HTTP query to FastAPI backend server.

    Parameters
    ----------
    raw_query : User query text.
    jurisdiction : Target jurisdiction string.
    formulation_category : Formulation category string.
    user_language : Optional ISO language code.
    api_base_url : Base URL for FastAPI server.

    Returns
    -------
    Dict[str, Any]
        Parsed JSON response dictionary from API.
    """
    url = f"{api_base_url.rstrip('/')}/query"
    payload = {
        "raw_query": raw_query,
        "jurisdiction": jurisdiction,
        "formulation_category": formulation_category,
        "user_language": user_language if user_language != "auto" else None,
    }

    response = httpx.post(url, json=payload, timeout=60.0)
    response.raise_for_status()
    return response.json()


def render_sidebar() -> Dict[str, Any]:
    """Render sidebar filters and backend configuration."""
    st.sidebar.title("⚙️ Search & Filter Setup")

    api_url = st.sidebar.text_input(
        "Backend API Base URL",
        value=DEFAULT_API_BASE_URL,
        help="FastAPI backend host URL",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Jurisdiction & Domain")

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
    st.sidebar.subheader("🌐 Language Preference")

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
        "Query/Response Language",
        options=list(language_options.keys()),
        index=0,
    )
    user_lang = language_options[selected_lang_label]

    st.sidebar.markdown("---")
    st.sidebar.info(
        "**IP-SAKTI Sahayak v0.1.0**\n\n"
        "AI decision-support tool for Traditional Knowledge, Patents, AYUSH & ABS regulatory compliance."
    )

    return {
        "api_url": api_url,
        "jurisdiction": jurisdiction,
        "formulation": formulation,
        "user_lang": user_lang,
    }


def render_response(res: Dict[str, Any]) -> None:
    """Render query execution response cards, confidence scores, and evidence provenance."""
    is_abstention = res.get("is_abstention", False)
    answer = res.get("answer", "")
    confidence = res.get("confidence")
    evidence = res.get("evidence", [])
    citations = res.get("citations", [])
    agents_invoked = res.get("agents_invoked", [])
    disclaimer = res.get("disclaimer", "")

    # 1. Agent & Status Badges
    col1, col2, col3 = st.columns(3)
    with col1:
        agents_str = ", ".join(agents_invoked) if agents_invoked else "N/A"
        st.caption(f"**Agents Invoked**: `{agents_str}`")
    with col2:
        status_str = "⚠️ Safe Abstention" if is_abstention else "✅ Source-Grounded"
        st.caption(f"**Status**: {status_str}")
    with col3:
        score_val = f"{confidence['score']*100:.0f}%" if confidence and "score" in confidence else "N/A"
        st.caption(f"**Confidence**: `{score_val}`")

    # 2. Main Response Area
    if is_abstention:
        st.warning(f"### 🛡️ Safe Abstention & Facilitator Escalation\n\n{answer}")
        st.info(
            "ℹ️ **Human/IP Facilitator Pathway**: This query has been logged to the escalation queue. "
            "Our legal/regulatory domain experts will review the query context and evidence base."
        )
    else:
        st.markdown(f"### 📄 Response\n\n{answer}")

    # 3. Confidence Metrics Breakdown
    if confidence:
        with st.expander("📊 Confidence & Verification Metrics", expanded=False):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall Score", f"{confidence.get('score', 0)*100:.1f}%")
            m2.metric("Evidence Chunks", confidence.get("evidence_count", 0))
            m3.metric("Citation Coverage", f"{confidence.get('citation_coverage', 0)*100:.0f}%")
            m4.metric("Avg Rerank Score", f"{confidence.get('avg_rerank_score', 0):.2f}")
            if confidence.get("reason"):
                st.caption(f"*Assessment Reason*: {confidence['reason']}")

    # 4. Evidence Chunks & Provenance Accordion
    if evidence:
        with st.expander(f"📚 Retrieved Evidence ({len(evidence)} Chunks)", expanded=False):
            for i, chunk in enumerate(evidence, 1):
                label = chunk.get("source_label", f"[SOURCE_{i}]")
                title = chunk.get("title", "Untitled Document")
                source_name = chunk.get("source_name", "Unknown Source")
                authority = chunk.get("authority", "N/A")
                content = chunk.get("content", "")
                url = chunk.get("source_url")

                st.markdown(f"#### {label} — {title}")
                st.caption(f"**Authority**: {authority} | **Source**: {source_name}")
                if url:
                    st.markdown(f"[🔗 View Source Document]({url})")
                st.info(content)
                st.markdown("---")

    # 5. Disclaimer Notice
    if disclaimer:
        st.caption(f"**Disclaimer**: {disclaimer}")


def main() -> None:
    """Main Streamlit application entry point."""
    st.title("📜 IP-SAKTI Sahayak")
    st.subheader("Multilingual Traditional Knowledge & Intellectual Property Decision Support System")

    filters = render_sidebar()

    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                render_response(msg["content"])

    # Query Input area
    prompt = st.chat_input("Ask a question about Traditional Knowledge, Patents, AYUSH licensing, or ABS...")
    if prompt:
        # Display user input in UI
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process via backend API
        with st.chat_message("assistant"):
            with st.spinner("Analyzing query, evaluating rules, and retrieving grounded evidence..."):
                try:
                    res = query_backend_api(
                        raw_query=prompt,
                        jurisdiction=filters["jurisdiction"],
                        formulation_category=filters["formulation"],
                        user_language=filters["user_lang"],
                        api_base_url=filters["api_url"],
                    )
                    st.session_state.messages.append({"role": "assistant", "content": res})
                    render_response(res)
                except Exception as exc:
                    err_msg = (
                        f"Unable to communicate with API backend at `{filters['api_url']}`.\n\n"
                        f"Details: `{exc}`\n\n"
                        "Please verify the FastAPI backend server is running."
                    )
                    st.error(err_msg)


if __name__ == "__main__":
    main()
