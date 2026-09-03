"""
ip_sakti.llm.gemini_adapter — Gemini LLM API Adapter.

Isolated interface for LLM answer generation using Google Gemini (google-generativeai).
Approved per AGENTS.md §5: LLM is a pretrained instruction-tuned model (Google Gemini via API).
Never hard-codes API keys; uses GEMINI_API_KEY environment variable.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Sequence

import yaml
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

from ip_sakti.models.query import EvidenceChunk, QueryContext
from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "config" / "prompts" / "answer_prompt.yaml"


class GeminiLLMAdapter:
    """
    Adapter wrapper for Google Gemini LLM API.

    Parameters
    ----------
    model_name :
        Gemini model name. Defaults to models.llm_model from config/settings.yaml
        or GEMINI_MODEL env var.
    api_key :
        Optional API key override. Defaults to GEMINI_API_KEY env var.
    """

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialise Gemini LLM adapter."""
        cfg = get_settings()
        self.model_name = (
            model_name
            or os.getenv("GEMINI_MODEL")
            or cfg.get("models", {}).get("llm_model", "gemini-1.5-flash")
        )
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        self.system_prompt = self._load_system_prompt()
        self._configured = False

        if self.api_key and _GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self._configured = True
            except Exception as exc:
                logger.warning(f"Failed to configure google.generativeai: {exc}")

    def _load_system_prompt(self) -> str:
        """Load anti-fabrication system prompt from answer_prompt.yaml."""
        if _PROMPT_PATH.exists():
            try:
                with _PROMPT_PATH.open("r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                return data.get("system_prompt", "")
            except Exception as exc:
                logger.warning(f"Failed to load system prompt: {exc}")
        return (
            "You are IP-SAKTI Sahayak, an AI assistant for IP and regulatory guidance in Ayurveda. "
            "You MUST ground all factual statements strictly in the provided evidence citations."
        )

    def generate_answer(
        self,
        context: QueryContext,
        evidence: Sequence[EvidenceChunk],
        applied_rules: Sequence[str] | None = None,
    ) -> str:
        """
        Generate a source-grounded answer using the LLM.

        Parameters
        ----------
        context :
            Enriched QueryContext model.
        evidence :
            List of retrieved EvidenceChunk instances.
        applied_rules :
            Domain guidance rules.

        Returns
        -------
        str
            Generated answer text containing source citations.
        """
        if not evidence:
            return "No sufficient evidence found to answer this query."

        # Format evidence blocks
        evidence_passages = []
        for idx, chunk in enumerate(evidence, start=1):
            label = chunk.source_label or f"[SOURCE_{idx}]"
            evidence_passages.append(
                f"{label} ({chunk.source_name}): {chunk.content}"
            )
        formatted_evidence = "\n\n".join(evidence_passages)

        user_prompt = (
            f"User Query: {context.translated_query}\n\n"
            f"Retrieved Evidence:\n{formatted_evidence}\n\n"
            f"Instructions: Provide a clear, factual answer to the query citing source labels "
            f"like [SOURCE_1], [SOURCE_2] for every factual statement. Do NOT make claims "
            f"unsupported by the provided evidence."
        )

        if self._configured and _GENAI_AVAILABLE:
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=self.system_prompt,
                )
                response = model.generate_content(user_prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                logger.error(f"Gemini API call failed: {exc}")

        # Fallback response generation when API key is unconfigured or in test mode
        summary_claims = []
        for idx, chunk in enumerate(evidence, start=1):
            label = chunk.source_label or f"[SOURCE_{idx}]"
            summary_claims.append(f"Based on {chunk.source_name} {label}: {chunk.content[:150]}...")

        return " ".join(summary_claims)
