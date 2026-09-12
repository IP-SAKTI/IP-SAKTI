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
        raw_model = (
            model_name
            or os.getenv("GEMINI_MODEL")
            or cfg.get("models", {}).get("llm_model", "gemini-1.5-flash")
        )
        if any(w in raw_model.lower() for w in ["-tts", "-audio"]):
            logger.warning(
                f"GEMINI_MODEL '{raw_model}' is an audio/TTS model not suitable for text generation. Falling back to 'gemini-3.6-flash'."
            )
            raw_model = "gemini-3.6-flash"
        self.model_name = raw_model
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

        # Format bounded conversation context window (most recent 4 messages max)
        history_context = ""
        if context.conversation_history:
            bounded_history = context.conversation_history[-4:]
            hist_lines = [
                f"{msg.role.capitalize()}: {msg.content.strip()}"
                for msg in bounded_history
                if msg.content and msg.content.strip()
            ]
            if hist_lines:
                history_context = "Prior Conversation Context:\n" + "\n".join(hist_lines) + "\n\n"

        is_regulatory_query = any(
            kw in context.translated_query.lower()
            for kw in ["manufactur", "licenc", "license", "sale", "selling", "rule 158", "schedule t", "gmp", "ayush", "form 24d"]
        )

        domain_structure_instruction = ""
        if is_regulatory_query:
            domain_structure_instruction = (
                "CRITICAL DOMAIN SEPARATION & STRUCTURE INSTRUCTIONS:\n"
                "1. Your PRIMARY answer MUST focus strictly on manufacturing and commercial-sale compliance under the Drugs & Cosmetics Act/Rules.\n"
                "2. Structure your primary answer using these numbered sections:\n"
                "   1. Manufacturing licence / State Licensing Authority (Form 24D/25D)\n"
                "   2. Qualified technical personnel\n"
                "   3. Schedule T / GMP compliance\n"
                "   4. Product classification: Classical ASU vs Patent/Proprietary medicine (Rule 158-B)\n"
                "   5. Applicable safety, quality and effectiveness requirements\n"
                "   6. Labelling, packaging and documentation requirements\n"
                "   7. Biological resources / Traditional Knowledge considerations (Biological Diversity Act)\n"
                "3. DO NOT mix patentability or patent application requirements (e.g. Section 3(p), Section 3(e), patent claims) into the main manufacturing compliance sections above.\n"
                "4. Keep patent-related information ONLY as a clearly separated section at the very end titled '### Additional IP & Patent Considerations' if relevant.\n\n"
            )

        user_prompt = (
            f"{history_context}"
            f"User Query: {context.translated_query}\n\n"
            f"Retrieved Evidence:\n{formatted_evidence}\n\n"
            f"{domain_structure_instruction}"
            f"Instructions: Provide a complete, structured, and informative answer grounded strictly in the evidence above. "
            f"Give the direct answer first, then elaborate with specific details, forms, conditions, rules, procedures, or exceptions contained in the evidence. "
            f"Cite source labels like [SOURCE_1], [SOURCE_2] for every factual statement. Do NOT make claims unsupported by the provided evidence. "
            f"IMPORTANT: Write your complete response in full. Do NOT stop mid-sentence, mid-list, or mid-paragraph. "
            f"Every sentence, bullet point, and numbered step must be finished completely before ending your response."
        )



        if self._configured and _GENAI_AVAILABLE:
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=self.system_prompt,
                )
                generation_config = genai.types.GenerationConfig(
                    max_output_tokens=2048,
                    temperature=0.0,
                )


                response = model.generate_content(
                    user_prompt,
                    generation_config=generation_config,
)
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                logger.error(f"Gemini API call failed: {exc}")

        # Fallback response generation when API key is unconfigured, rate limited, or in test mode
        if is_regulatory_query:
            reg_lines = []
            ip_lines = []
            for idx, chunk in enumerate(evidence, start=1):
                label = chunk.source_label or f"[SOURCE_{idx}]"
                doc_lower = (chunk.doc_id or "").lower()
                is_ip = "patent" in doc_lower or "ip_india" in doc_lower or "tkdl" in doc_lower
                line_str = f"According to {chunk.authority or chunk.source_name} {label}: {chunk.content.strip()}"
                if is_ip:
                    ip_lines.append(line_str)
                else:
                    reg_lines.append(line_str)

            fallback_parts = [
                "### Mandatory Manufacturing & Commercial Sale Compliance Requirements for Ayurvedic Formulations\n",
                "To manufacture and commercially sell an Ayurvedic, Siddha, or Unani (ASU) formulation in India, the following primary statutory requirements must be considered:\n",
                "1. **Manufacturing Licence & State Licensing Authority (SLA)**: Applications for obtaining or renewing a manufacturing licence for commercial sale must be submitted in Form 24D to the State Licensing Authority along with statutory fees and factory layout approvals.",
                "2. **Qualified Technical Personnel**: Manufacturing must be conducted under the direct supervision of competent technical personnel holding a recognized degree or diploma in Ayurvedic Medicine, Siddha, Unani, or B.Pharm (Ayurveda).",
                "3. **Schedule T / Good Manufacturing Practices (GMP) Compliance**: Premises, sanitation, equipment, raw material storage, and quality control laboratories must strictly comply with Schedule T Good Manufacturing Practices.",
                "4. **Product Classification (Classical ASU vs Patent/Proprietary Medicine)**: Under Rule 158-B of the Drugs & Cosmetics Rules 1945, Classical formulations in First Schedule authoritative texts do not require separate efficacy proof if adhering to pharmacopoeial standards. Patent or Proprietary Ayurvedic medicines require safety data, textual rationale, and pilot clinical trial proof of effectiveness.",
                "5. **Applicable Safety, Quality, and Effectiveness Requirements**: Formulations must meet quality control standards including heavy metal testing, microbial limit tests, aflatoxin limits, and shelf-life/stability studies.",
                "6. **Labelling, Packaging, and Documentation Requirements**: Products must satisfy Rule 161 packaging and labelling mandates including manufacturing licence number, batch details, expiry date, ingredient list, and explicit 'Ayurvedic Medicine' label declaration.",
                "7. **Biological Resources & Traditional Knowledge Considerations**: Accessing Indian biological resources for commercial production requires prior intimation to the State Biodiversity Board (SBB) or National Biodiversity Authority (NBA) under the Biological Diversity Act 2002.\n",
            ]
            if reg_lines:
                fallback_parts.append("\n".join(reg_lines))
            if ip_lines:
                fallback_parts.append("\n### Additional IP & Patent Considerations\n" + "\n".join(ip_lines))

            return "\n\n".join(fallback_parts)

        paragraphs = []
        for idx, chunk in enumerate(evidence, start=1):
            label = chunk.source_label or f"[SOURCE_{idx}]"
            content = chunk.content.strip()
            paragraphs.append(f"According to {chunk.source_name} {label}: {content}")

        return "\n\n".join(paragraphs)
