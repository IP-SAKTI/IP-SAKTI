"""
Voice Input / Speech-to-Text & Multilingual Translation Service for IP-SAKTI Sahayak

Uses pretrained Whisper 'base' model with deterministic greedy decoding (temperature=0.0),
task="transcribe" for native script decoding (EN, HI, TE, KN) with native script prompts,
anti-romanization validation, and QueryTranslator for semantic English translation.
"""

import os
import sys
import shutil
import tempfile
import logging

logger = logging.getLogger(__name__)

# Ensure ffmpeg binary from imageio-ffmpeg is copied as ffmpeg.exe and added to PATH
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    target_ffmpeg = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    if not os.path.exists(target_ffmpeg) and os.path.exists(ffmpeg_exe):
        try:
            shutil.copy2(ffmpeg_exe, target_ffmpeg)
            logger.info(f"Copied {ffmpeg_exe} -> {target_ffmpeg}")
        except Exception as copy_err:
            logger.warning(f"Could not copy ffmpeg.exe: {copy_err}")
            
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")
        logger.info(f"Added ffmpeg directory to PATH: {ffmpeg_dir}")
except Exception as e:
    logger.warning(f"Could not load imageio-ffmpeg helper: {e}")

_WHISPER_MODEL = None
_QUERY_TRANSLATOR = None

SUPPORTED_VOICE_LANGUAGES = {"en", "hi", "te", "kn"}

LANG_CODE_MAP = {
    "en": "en", "eng": "en", "english": "en",
    "hi": "hi", "hin": "hi", "hindi": "hi",
    "te": "te", "tel": "te", "telugu": "te",
    "kn": "kn", "kan": "kn", "kannada": "kn",
}

INDIC_NATIVE_PROMPT = (
    "What permissions are required to manufacture an Ayurvedic medicine? "
    "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి? "
    "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए? "
    "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"
)

COMMON_ENGLISH_KEYWORDS = {
    "what", "how", "which", "why", "where", "is", "are", "can", "to", "for",
    "in", "of", "and", "the", "a", "an", "permission", "permissions", "license",
    "licence", "manufacture", "manufacturing", "make", "selling", "product",
    "medicine", "drug", "ayurvedic", "ayurveda", "formulation", "requirement",
    "requirements", "rule", "rules", "act", "patent", "patents"
}


def get_whisper_model(model_name: str = "base"):
    """
    Lazy-load and return cached singleton instance of Whisper model.
    Default: 'base' for high-accuracy CPU transcription & translation.
    """
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        logger.info(f"Loading Whisper model '{model_name}'...")
        import whisper
        _WHISPER_MODEL = whisper.load_model(model_name)
        logger.info(f"Whisper model '{model_name}' loaded successfully.")
    return _WHISPER_MODEL


def get_query_translator():
    """
    Lazy-load and return cached singleton instance of QueryTranslator.
    """
    global _QUERY_TRANSLATOR
    if _QUERY_TRANSLATOR is None:
        from ip_sakti.multilingual.translator import QueryTranslator
        _QUERY_TRANSLATOR = QueryTranslator()
    return _QUERY_TRANSLATOR


def is_romanized_gibberish(text: str, source_lang: str) -> bool:
    """
    Detect if text is romanized/transliterated non-English tokens instead of
    true English semantic translation.
    """
    if not text or source_lang == "en":
        return False
        
    text_lower = text.lower()
    
    # Check for known romanized non-English tokens
    romanized_tokens = {"hairovidha", "haushdha", "hayaro", "tanki", "inhon", "madho", "kowali", "banane", "chahiye", "tayaru", "cheyadaniki"}
    words = set(text_lower.split())
    if len(words.intersection(romanized_tokens)) > 0:
        return True

    # If length > 15 chars, genuine English translation should contain common English words/keywords
    if len(text_lower) > 15:
        overlap = words.intersection(COMMON_ENGLISH_KEYWORDS)
        if len(overlap) == 0:
            return True

    return False


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe audio bytes using pretrained Whisper model ('base') with task='transcribe'.
    Decodes native script (EN, HI, TE, KN) and produces semantic English translation.
    
    Args:
        audio_bytes: Raw bytes of the recorded audio file.
        filename: Original filename or hint for format extension.
        
    Returns:
        dict: {
            "transcript": str,
            "language": str,
            "translated_text": str | None,
            "error": str | None
        }
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return {
            "transcript": "",
            "language": "en",
            "translated_text": None,
            "error": "Audio recording is empty or too short. Please speak again."
        }

    ext = os.path.splitext(filename)[1]
    if not ext or len(ext) > 10:
        ext = ".webm"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_whisper_model("base")

        # Step 1: STT Transcription in native script using task="transcribe" and native script initial prompt
        stt_result = model.transcribe(
            tmp_path,
            fp16=False,
            task="transcribe",
            temperature=0.0,
            initial_prompt=INDIC_NATIVE_PROMPT,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.4
        )

        raw_text = stt_result.get("text", "").strip()
        raw_lang = (stt_result.get("language") or "en").lower().strip()
        norm_lang = LANG_CODE_MAP.get(raw_lang, raw_lang)

        logger.info(f"Whisper STT transcript: '{raw_text}' (raw_lang={raw_lang}, norm_lang={norm_lang})")

        # Reject empty or no-speech audio
        if not raw_text:
            return {
                "transcript": "",
                "language": norm_lang if norm_lang in SUPPORTED_VOICE_LANGUAGES else "en",
                "translated_text": None,
                "error": "No speech detected in audio. Please try speaking clearly."
            }

        # Language validation: reject unsupported languages
        if norm_lang not in SUPPORTED_VOICE_LANGUAGES:
            logger.warning(f"Unsupported voice language detected: '{norm_lang}'")
            return {
                "transcript": "",
                "language": "unsupported",
                "translated_text": None,
                "error": "Unsupported voice language"
            }

        # English voice query: transcript and translated_text are identical
        if norm_lang == "en":
            return {
                "transcript": raw_text,
                "language": "en",
                "translated_text": raw_text,
                "error": None
            }

        # Step 2: Semantic Translation to English for Indian Languages (hi, te, kn)
        translated_text = None

        # Route A: QueryTranslator semantic translation (primary for native script)
        try:
            translator = get_query_translator()
            qt_res = translator.translate_to_retrieval_language(raw_text, norm_lang)
            candidate = qt_res.translated_text.strip() if qt_res and qt_res.translated_text else ""
            if candidate and not is_romanized_gibberish(candidate, norm_lang):
                translated_text = candidate
                logger.info(f"QueryTranslator produced semantic translation: '{translated_text}'")
        except Exception as qt_err:
            logger.warning(f"QueryTranslator error: {qt_err}")

        # Route B: Direct neural audio-to-English translation task ("translate") via Whisper if Route A failed
        if not translated_text or is_romanized_gibberish(translated_text, norm_lang):
            try:
                whisper_trans = model.transcribe(
                    tmp_path,
                    fp16=False,
                    task="translate",
                    temperature=0.0,
                    condition_on_previous_text=False
                )
                whisper_candidate = whisper_trans.get("text", "").strip()
                if whisper_candidate and not is_romanized_gibberish(whisper_candidate, norm_lang):
                    translated_text = whisper_candidate
                    logger.info(f"Whisper task=translate produced semantic translation: '{translated_text}'")
            except Exception as w_err:
                logger.warning(f"Whisper translate task error: {w_err}")

        # Final Fallback check
        if not translated_text or is_romanized_gibberish(translated_text, norm_lang):
            logger.warning(f"Translation failed or produced romanization for [{norm_lang}] '{raw_text}'")
            return {
                "transcript": raw_text,
                "language": norm_lang,
                "translated_text": None,
                "error": "Translation failed: Could not produce valid English translation."
            }

        return {
            "transcript": raw_text,
            "language": norm_lang,
            "translated_text": translated_text,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error during audio processing: {e}", exc_info=True)
        return {
            "transcript": "",
            "language": "en",
            "translated_text": None,
            "error": f"Voice processing failed: {str(e)}"
        }
    finally:
        # Immediate cleanup of temporary audio file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
