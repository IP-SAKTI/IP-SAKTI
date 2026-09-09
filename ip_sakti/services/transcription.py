"""
Voice Input / Speech-to-Text & Multilingual Translation Service for IP-SAKTI Sahayak

Uses pretrained Whisper 'base' model with deterministic greedy decoding (temperature=0.0),
anti-hallucination constraints, and safe language detection filtering for English, Hindi,
Telugu, and Kannada. Integrates with QueryTranslator for translating voice queries.
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


def get_whisper_model(model_name: str = "base"):
    """
    Lazy-load and return cached singleton instance of Whisper model.
    Default: 'base' for high-accuracy CPU transcription.
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


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe audio bytes using pretrained Whisper model ('base') with deterministic
    greedy decoding (temperature=0.0) and translate to English if language is one of the
    supported Indian languages (hi, te, kn).
    
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

        # Robust, deterministic decoding options to prevent hallucination & bad sampling
        result = model.transcribe(
            tmp_path,
            fp16=False,
            task="transcribe",
            temperature=0.0,                    # Deterministic greedy decoding (eliminates random sampling hallucinations)
            condition_on_previous_text=False,  # Prevents hallucinating text from silence/previous clips
            no_speech_threshold=0.6,           # Rejects audio segments where no-speech probability > 0.6
            logprob_threshold=-1.0,            # Rejects low confidence logprob outputs
            compression_ratio_threshold=2.4    # Detects repetitive/hallucinated text loops
        )

        raw_text = result.get("text", "").strip()
        raw_lang = (result.get("language") or "en").lower().strip()
        norm_lang = LANG_CODE_MAP.get(raw_lang, raw_lang)

        logger.info(f"Whisper STT decoded: '{raw_text}' (raw_lang={raw_lang}, norm_lang={norm_lang})")

        # 1. Reject empty or no-speech transcript
        if not raw_text:
            return {
                "transcript": "",
                "language": norm_lang if norm_lang in SUPPORTED_VOICE_LANGUAGES else "en",
                "translated_text": None,
                "error": "No speech detected in audio. Please try speaking clearly."
            }

        # 2. Strict language filter: if Whisper detects an unsupported language (e.g. 'pa', 'cy', 'ja')
        if norm_lang not in SUPPORTED_VOICE_LANGUAGES:
            logger.warning(f"Unsupported voice language detected: '{norm_lang}' for text '{raw_text}'")
            return {
                "transcript": "",
                "language": "unsupported",
                "translated_text": None,
                "error": "Unsupported voice language"
            }

        # 3. English voice query
        if norm_lang == "en":
            return {
                "transcript": raw_text,
                "language": "en",
                "translated_text": raw_text,
                "error": None
            }

        # 4. Multilingual voice query (Hindi, Telugu, Kannada) -> translate to English
        try:
            translator = get_query_translator()
            trans_result = translator.translate_to_retrieval_language(raw_text, norm_lang)
            translated = trans_result.translated_text.strip()
            
            logger.info(f"Translated [{norm_lang}] '{raw_text}' -> [en] '{translated}'")
            
            return {
                "transcript": raw_text,
                "language": norm_lang,
                "translated_text": translated if translated else raw_text,
                "error": None
            }
        except Exception as trans_err:
            logger.error(f"Translation failed for [{norm_lang}] text '{raw_text}': {trans_err}", exc_info=True)
            return {
                "transcript": raw_text,
                "language": norm_lang,
                "translated_text": None,
                "error": f"Translation failed: {str(trans_err)}"
            }

    except Exception as e:
        logger.error(f"Error during audio transcription: {e}", exc_info=True)
        return {
            "transcript": "",
            "language": "en",
            "translated_text": None,
            "error": f"Transcription failed: {str(e)}"
        }
    finally:
        # Immediate cleanup of temporary audio file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
