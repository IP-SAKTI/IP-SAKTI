"""
ip_sakti.multilingual.translator — Translation component.

Handles translation between supported user languages and the internal
retrieval language (English).

Pipeline:

    User Language
          ↓
    English for RAG / LLM
          ↓
    English Answer
          ↓
    User Language

Citation markers such as [SOURCE_1] are preserved during translation.
"""

from __future__ import annotations

import logging
import re

from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    NotValidPayload,
    RequestError,
    TranslationNotFound,
)

from ip_sakti.llm.gemini_adapter import GeminiLLMAdapter
from ip_sakti.models.multilingual import TranslationResult
from ip_sakti.multilingual.exceptions import (
    TranslationError,
    UnsupportedLanguageError,
)
from ip_sakti.multilingual.language_registry import (
    LanguageRegistry,
    get_language_registry,
)

logger = logging.getLogger(__name__)


# Matches citation markers such as:
# [SOURCE_1]
# [SOURCE_2]
# [SOURCE_15]
_CITATION_PATTERN = re.compile(r"\[SOURCE_\d+\]")


class QueryTranslator:
    """
    Translates queries and responses between supported languages.

    Uses Gemini TEXT MODEL (gemini-3.6-flash) as primary provider with
    script validation and deep-translator as secondary fallback.
    """

    def __init__(
        self,
        registry: LanguageRegistry | None = None,
    ) -> None:
        """Initialise the translator."""
        self._registry = registry or get_language_registry()

        try:
            self._gemini = GeminiLLMAdapter()
        except Exception as exc:
            logger.warning(f"Could not initialize GeminiLLMAdapter for QueryTranslator: {exc}")
            self._gemini = None

        logger.debug(
            "QueryTranslator initialised",
            extra={
                "retrieval_language": self._registry.retrieval_language,
                "supported_languages": sorted(self._registry.supported_codes),
            },
        )

    # ==================================================================
    # QUERY TRANSLATION
    # ==================================================================

    def translate_to_retrieval_language(
        self,
        text: str,
        source_language: str,
    ) -> TranslationResult:
        """
        Translate a user query into natural English using Gemini TEXT MODEL.
        """
        source = source_language.lower().strip()
        target = self._registry.retrieval_language

        self._validate_language(source)

        if source == target:
            return TranslationResult(
                source_language=source,
                target_language=target,
                original_text=text,
                translated_text=text,
                was_translated=False,
            )

        # 1. Primary: Gemini TEXT MODEL Translation
        gemini_translated = self._translate_with_gemini(text, source, target, is_query=True)
        if gemini_translated:
            logger.info(f"[QUERY_TRANSLATION] source={source} target={target} model=gemini-3.6-flash success=true")
            logger.info(f"[NORMALIZED_QUERY] {gemini_translated}")
            return TranslationResult(
                source_language=source,
                target_language=target,
                original_text=text,
                translated_text=gemini_translated,
                was_translated=True,
            )

        # 2. Fallback: GoogleTranslate
        return self._translate(
            text=text,
            source_language=source,
            target_language=target,
        )

    # ==================================================================
    # RESPONSE TRANSLATION
    # ==================================================================

    def translate_response(
        self,
        text: str,
        target_language: str,
    ) -> TranslationResult:
        """
        Translate an English answer back into the user's language using Gemini TEXT MODEL.
        """
        source = self._registry.retrieval_language
        target = target_language.lower().strip()

        self._validate_language(target)

        if source == target:
            return TranslationResult(
                source_language=source,
                target_language=target,
                original_text=text,
                translated_text=text,
                was_translated=False,
            )

        return self._translate_response_with_citations(
            text=text,
            source_language=source,
            target_language=target,
        )

    # ==================================================================
    # LANGUAGE VALIDATION & SCRIPT VALIDATION
    # ==================================================================

    def _validate_language(self, code: str) -> None:
        """Validate that the language is supported."""
        if code == self._registry.retrieval_language:
            return

        if not self._registry.is_supported(code):
            raise UnsupportedLanguageError(
                f"Language {code!r} is not supported by IP-SAKTI. "
                f"Supported languages: {sorted(self._registry.supported_codes)}"
            )

    @staticmethod
    def _validate_target_script(text: str, target_lang: str) -> bool:
        """Verify that translated text contains native Unicode characters for target language."""
        clean_code = target_lang.lower().strip()
        if clean_code in ("en", "english"):
            return True

        script_ranges = {
            "kn": (0x0C80, 0x0CFF),  # Kannada
            "te": (0x0C00, 0x0C7F),  # Telugu
            "hi": (0x0900, 0x097F),  # Devanagari (Hindi)
            "mr": (0x0900, 0x097F),  # Devanagari (Marathi)
            "ta": (0x0B80, 0x0BFF),  # Tamil
            "ml": (0x0D00, 0x0D7F),  # Malayalam
            "bn": (0x0980, 0x09FF),  # Bengali
            "gu": (0x0A80, 0x0AFF),  # Gujarati
            "pa": (0x0A00, 0x0A7F),  # Gurmukhi
        }

        rng = script_ranges.get(clean_code)
        if not rng:
            return True

        start, end = rng
        match_count = sum(1 for char in text if start <= ord(char) <= end)
        clean_text = text.replace(" ", "").replace("\n", "")
        total_len = len(clean_text)
        return match_count >= 3 or (total_len > 0 and (match_count / total_len) >= 0.05)

    # ==================================================================
    # GEMINI TRANSLATION
    # ==================================================================

    def _translate_with_gemini(
        self,
        text: str,
        source_language: str,
        target_language: str,
        is_query: bool = True,
        strict_retry: bool = False,
    ) -> str | None:
        """Translate text using Gemini TEXT MODEL (gemini-3.6-flash)."""
        if not self._gemini or not self._gemini._configured:
            return None

        lang_names = {
            "kn": ("Kannada", "Kannada Unicode Script"),
            "te": ("Telugu", "Telugu Unicode Script"),
            "hi": ("Hindi", "Devanagari Script"),
            "ta": ("Tamil", "Tamil Unicode Script"),
            "ml": ("Malayalam", "Malayalam Unicode Script"),
            "mr": ("Marathi", "Devanagari Script"),
            "bn": ("Bengali", "Bengali Unicode Script"),
            "gu": ("Gujarati", "Gujarati Unicode Script"),
            "pa": ("Punjabi", "Gurmukhi Script"),
            "en": ("English", "Latin Script"),
        }

        src_name, _ = lang_names.get(source_language.lower(), (source_language, ""))
        tgt_name, tgt_script = lang_names.get(target_language.lower(), (target_language, ""))

        if is_query:
            prompt = (
                "Translate the following user question into natural English.\n"
                "Do not answer the question.\n"
                "Do not explain.\n"
                "Do not summarize.\n"
                "Return only the English translation.\n\n"
                f"Query: {text}"
            )
        else:
            if strict_retry:
                prompt = (
                    f"STRICT TRANSLATION MANDATE: Translate the following legal and regulatory guidance text into native {tgt_name} script ({tgt_script}).\n"
                    f"CRITICAL MANDATES:\n"
                    f"1. You MUST write your complete translation in native {tgt_name} script ({tgt_script}).\n"
                    f"2. Do NOT use Latin/Roman alphabet or English transliteration.\n"
                    f"3. Keep all [SOURCE_1], [SOURCE_2] citation tags intact.\n"
                    f"4. Return ONLY the translated response in native {tgt_name} script.\n\n"
                    f"Text: {text}"
                )
            else:
                prompt = (
                    f"Translate the following legal and regulatory answer text from English into native {tgt_name} script ({tgt_script}).\n"
                    f"CRITICAL MANDATES:\n"
                    f"1. Write the response in native {tgt_name} script.\n"
                    f"2. Do NOT use Latin/Roman alphabet or transliteration.\n"
                    f"3. Keep all [SOURCE_1], [SOURCE_2] citation tags intact.\n\n"
                    f"Text: {text}"
                )

        sys_inst = (
            "You are an expert legal and regulatory translator for IP-SAKTI. "
            "Your task is to translate text accurately into the requested language and script.\n"
            "CRITICAL MANDATES:\n"
            "1. Do NOT include commentary, reasoning, self-reflection, or internal thoughts.\n"
            "2. Output ONLY the raw translated text.\n"
            "3. Preserve all markdown structure and citation tags like [SOURCE_1] exactly as they appear."
        )

        try:
            import google.generativeai as genai
            model = genai.GenerativeModel(model_name=self._gemini.model_name, system_instruction=sys_inst)
            gen_cfg = genai.types.GenerationConfig(temperature=0.0, max_output_tokens=4096)
            res = model.generate_content(prompt, generation_config=gen_cfg)
            if res and res.text:
                out_text = res.text.strip()
                if out_text:
                    return out_text
        except Exception as err:
            logger.debug(f"Gemini translation call failed ({source_language} -> {target_language}): {err}")
        return None

    # ==================================================================
    # GENERAL TRANSLATION & CITATION PRESERVATION
    # ==================================================================

    def _translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Perform fallback translation via deep-translator."""
        if source_language == target_language:
            return TranslationResult(
                source_language=source_language,
                target_language=target_language,
                original_text=text,
                translated_text=text,
                was_translated=False,
            )

        translated_text = self._call_google_translate(
            text=text,
            source=source_language,
            target=target_language,
        )

        return TranslationResult(
            source_language=source_language,
            target_language=target_language,
            original_text=text,
            translated_text=translated_text,
            was_translated=True,
        )

    def _translate_response_with_citations(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Translate an answer while preserving [SOURCE_X] citations and validating target script."""
        if source_language == target_language:
            return TranslationResult(
                source_language=source_language,
                target_language=target_language,
                original_text=text,
                translated_text=text,
                was_translated=False,
            )

        model_used = self._gemini.model_name if self._gemini else "gemini-3.6-flash"

        # 1. Primary: Gemini TEXT MODEL Translation
        gemini_translated = self._translate_with_gemini(text, source_language, target_language, is_query=False, strict_retry=False)
        if gemini_translated and self._validate_target_script(gemini_translated, target_language):
            logger.info(f"[ANSWER_TRANSLATION] source={source_language} target={target_language} model={model_used} success=true")
            logger.info(f"[TARGET_SCRIPT_VALIDATION] language={target_language} valid=true")
            return TranslationResult(
                source_language=source_language,
                target_language=target_language,
                original_text=text,
                translated_text=gemini_translated,
                was_translated=True,
            )

        # 2. Strict Retry via Gemini (Target Script Mandate)
        logger.info(f"[ANSWER_TRANSLATION] Retrying Gemini translation with strict script mandate for {target_language}")
        strict_translated = self._translate_with_gemini(text, source_language, target_language, is_query=False, strict_retry=True)
        if strict_translated and self._validate_target_script(strict_translated, target_language):
            logger.info(f"[ANSWER_TRANSLATION] source={source_language} target={target_language} model={model_used}_strict_retry success=true")
            logger.info(f"[TARGET_SCRIPT_VALIDATION] language={target_language} valid=true")
            return TranslationResult(
                source_language=source_language,
                target_language=target_language,
                original_text=text,
                translated_text=strict_translated,
                was_translated=True,
            )

        # 3. Secondary Fallback: GoogleTranslate (deep-translator) with citation placeholders
        citations: list[str] = []

        def replace_citation(match: re.Match[str]) -> str:
            index = len(citations)
            citations.append(match.group(0))
            return f" CITATIONPLACEHOLDER{index} "

        protected_text = _CITATION_PATTERN.sub(replace_citation, text)

        try:
            fallback_translated = self._call_google_translate(
                text=protected_text,
                source=source_language,
                target=target_language,
            )
            # Restore citations
            for index, citation in enumerate(citations):
                placeholder_pattern = re.compile(rf"\s*CITATIONPLACEHOLDER\s*{index}\s*", re.IGNORECASE)
                fallback_translated = placeholder_pattern.sub(f" {citation} ", fallback_translated)
                if citation not in fallback_translated:
                    fallback_translated = fallback_translated.replace(f"CITATIONPLACEHOLDER{index}", citation)

            fallback_translated = re.sub(r"[ \t]+", " ", fallback_translated).strip()

            if self._validate_target_script(fallback_translated, target_language):
                logger.info(f"[ANSWER_TRANSLATION] source={source_language} target={target_language} model=google_translate_fallback success=true")
                logger.info(f"[TARGET_SCRIPT_VALIDATION] language={target_language} valid=true")
                return TranslationResult(
                    source_language=source_language,
                    target_language=target_language,
                    original_text=text,
                    translated_text=fallback_translated,
                    was_translated=True,
                )
        except Exception as fallback_err:
            logger.warning(f"Google translate fallback failed: {fallback_err}")

        # 4. Final Safe Fallback: Return original English answer safely with controlled translation warning
        logger.error(f"[TARGET_SCRIPT_VALIDATION] language={target_language} valid=false error=TRANSLATION_SCRIPT_VALIDATION_FAILED")
        return TranslationResult(
            source_language=source_language,
            target_language=target_language,
            original_text=text,
            translated_text=text,
            was_translated=False,
        )

    # ==================================================================
    # GOOGLE TRANSLATE
    # ==================================================================

    @staticmethod
    def _call_google_translate(
        text: str,
        source: str,
        target: str,
    ) -> str:
        """Call Google Translate through deep-translator with chunking for long texts (> 4000 chars)."""
        if len(text) > 4000:
            paragraphs = text.split("\n\n")
            translated_paragraphs = []
            for p in paragraphs:
                if p.strip():
                    try:
                        translator = GoogleTranslator(source=source, target=target)
                        res = translator.translate(p)
                        translated_paragraphs.append(res if res else p)
                    except Exception:
                        translated_paragraphs.append(p)
                else:
                    translated_paragraphs.append("")
            return "\n\n".join(translated_paragraphs)

        try:
            try:
                translator = GoogleTranslator(source=source, target=target)
                result = translator.translate(text)
            except Exception:
                translator = GoogleTranslator(source="auto", target=target)
                result = translator.translate(text)

            if result is None:
                raise TranslationError(f"GoogleTranslator returned no translation for {source!r} → {target!r}.")

            translated_text = str(result).strip()
            if not translated_text:
                raise TranslationError(f"GoogleTranslator returned an empty translation for {source!r} → {target!r}.")

            return translated_text

        except TranslationError:
            raise
        except Exception as exc:
            logger.error(f"Google translation failed ({source!r} → {target!r}): {exc}")
            raise TranslationError(f"Translation failed ({source!r} → {target!r}): {exc}") from exc