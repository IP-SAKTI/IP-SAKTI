"""
Voice Input / Speech-to-Text & Multilingual Translation Service for IP-SAKTI Sahayak

Uses pretrained Whisper 'base' model with 2-stage audio language detection,
explicit language enforcement (task='transcribe', language=norm_lang),
script consistency validation, and QueryTranslator for semantic English translation.
Includes verbose === VOICE DEBUG === output for empirical diagnosis.
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
    "en": "en", "eng": "en", "english": "en", "en-in": "en", "en-us": "en",
    "hi": "hi", "hin": "hi", "hindi": "hi", "hi-in": "hi", "ur": "hi", "mr": "hi", "pa": "hi", "ne": "hi", "bh": "hi", "sd": "hi",
    "te": "te", "tel": "te", "telugu": "te", "te-in": "te", "ta": "te", "si": "te",
    "kn": "kn", "kan": "kn", "kannada": "kn", "kn-in": "kn", "ml": "kn",
}

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


def validate_script_consistency(text: str, lang_code: str) -> bool:
    """
    Enforce strict script consistency for the detected language:
    - 'te' (Telugu) MUST contain Telugu script characters (\u0c00-\u0c7f).
    - 'kn' (Kannada) MUST contain Kannada script characters (\u0c80-\u0cff).
    - 'hi' (Hindi) MUST contain Devanagari script characters (\u0900-\u097f).
    """
    if not text or lang_code == "en":
        return True

    devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097f')
    telugu_count = sum(1 for c in text if '\u0c00' <= c <= '\u0c7f')
    kannada_count = sum(1 for c in text if '\u0c80' <= c <= '\u0cff')

    if lang_code == "te" and telugu_count == 0:
        logger.error(f"Script Mismatch / Hallucination: language='te' but zero Telugu characters in '{text}'")
        return False

    if lang_code == "kn" and kannada_count == 0:
        logger.error(f"Script Mismatch / Hallucination: language='kn' but zero Kannada characters in '{text}'")
        return False

    if lang_code == "hi" and devanagari_count == 0:
        logger.error(f"Script Mismatch / Hallucination: language='hi' but zero Devanagari characters in '{text}'")
        return False

    return True


def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    content_type: str = None,
    target_lang: str = None
) -> dict:
    """
    Transcribe audio bytes using pretrained Whisper model ('base').
    Uses explicit language enforcement (task='transcribe', language=norm_lang),
    and script consistency validation.
    
    Args:
        audio_bytes: Raw bytes of the recorded audio file.
        filename: Original filename or hint for format extension.
        content_type: MIME type of the uploaded audio file.
        target_lang: Optional target language code hint (en, hi, te, kn).
        
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

    mime = content_type or f"audio/{ext.lstrip('.')}"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        import whisper
        model = get_whisper_model("base")

        # ── Stage 1: Target Language Enforcement (Force User Selection) ────────────
        raw_lang = "en"
        detected_prob = 1.0

        if target_lang:
            hint_clean = LANG_CODE_MAP.get(target_lang.lower().strip(), target_lang.lower().strip())
            if hint_clean in SUPPORTED_VOICE_LANGUAGES:
                norm_lang = hint_clean
                raw_lang = norm_lang
                logger.info(f"Forcing user-selected STT language: '{norm_lang}'")
            else:
                norm_lang = "en"
        else:
            try:
                audio = whisper.load_audio(tmp_path)
                if len(audio) > 0:
                    audio_padded = whisper.pad_or_trim(audio)
                    mel = whisper.log_mel_spectrogram(audio_padded).to(model.device)
                    _, probs = model.detect_language(mel)
                    top_lang = max(probs, key=probs.get)
                    raw_lang = str(top_lang).lower().strip()
                    detected_prob = float(probs[top_lang])
                    logger.info(f"Whisper Audio Language Detection: raw_lang='{raw_lang}', prob={detected_prob:.4f}")
            except Exception as det_err:
                logger.warning(f"Whisper detect_language fallback error: {det_err}")

            norm_lang = LANG_CODE_MAP.get(raw_lang, raw_lang)
            if norm_lang not in SUPPORTED_VOICE_LANGUAGES:
                logger.warning(f"Unsupported language '{norm_lang}', defaulting to 'en'")
                norm_lang = "en"

        # ── Stage 2: Targeted STT Transcription with Explicit Language Enforcement ─
        stt_result = model.transcribe(
            tmp_path,
            fp16=False,
            task="transcribe",                  # Native speech-to-text ONLY
            language=norm_lang,                 # Explicitly enforce target language & script!
            temperature=0.0,                    # Greedy deterministic decoding
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.4
        )

        raw_text = stt_result.get("text", "").strip()
        logger.info(f"Whisper STT decoded (lang={norm_lang}): '{raw_text}'")

        # Reject empty or no-speech audio
        if not raw_text:
            return {
                "transcript": "",
                "language": norm_lang,
                "translated_text": None,
                "error": "No speech detected in audio. Please try speaking clearly."
            }

        # ── Stage 3: Script Consistency Validation ─────────────────────────────────
        if not validate_script_consistency(raw_text, norm_lang):
            logger.error(f"Script Mismatch / Hallucination Rejected: lang={norm_lang} cannot produce script of '{raw_text}'")
            lang_names = {"en": "English", "hi": "Hindi", "te": "Telugu", "kn": "Kannada"}
            l_name = lang_names.get(norm_lang, norm_lang)
            return {
                "transcript": "",
                "language": norm_lang,
                "translated_text": None,
                "error": f"Speech detected, but {l_name} transcription could not be completed (script mismatch). Please try speaking clearly."
            }

        # ── Stage 4: English vs Multilingual Semantic Translation ──────────────────
        if norm_lang == "en":
            # Print Verbose Diagnostic Log to Terminal for English
            print("\n" + "=" * 50, flush=True)
            print("=== VOICE DEBUG ===", flush=True)
            print(f"MIME: {mime}", flush=True)
            print(f"Size: {len(audio_bytes)} bytes", flush=True)
            print(f"Temp Audio Path: {tmp_path}", flush=True)
            print(f"\nWhisper detected:\n{raw_lang}\nprobability:\n{detected_prob:.2f}", flush=True)
            print(f"\nTranscription:\nlanguage={norm_lang}\ntask=transcribe", flush=True)
            print(f"\nRAW TRANSCRIPT:\n{raw_text}", flush=True)
            print(f"\nTRANSLATION INPUT:\n{raw_text}", flush=True)
            print(f"\nTRANSLATION OUTPUT:\n{raw_text}", flush=True)
            print("=" * 50 + "\n", flush=True)

            return {
                "transcript": raw_text,
                "language": "en",
                "translated_text": raw_text,
                "error": None
            }

        translated_text = None
        try:
            translator = get_query_translator()
            qt_res = translator.translate_to_retrieval_language(raw_text, norm_lang)
            candidate = qt_res.translated_text.strip() if qt_res and qt_res.translated_text else ""
            if candidate and not is_romanized_gibberish(candidate, norm_lang):
                translated_text = candidate
                logger.info(f"QueryTranslator produced semantic translation: '{translated_text}'")
        except Exception as qt_err:
            logger.warning(f"QueryTranslator error: {qt_err}")

        # Secondary translation route: Whisper built-in translate task
        if not translated_text or is_romanized_gibberish(translated_text, norm_lang):
            try:
                whisper_trans = model.transcribe(
                    tmp_path,
                    fp16=False,
                    task="translate",
                    language=norm_lang,
                    temperature=0.0,
                    condition_on_previous_text=False
                )
                whisper_candidate = whisper_trans.get("text", "").strip()
                if whisper_candidate and not is_romanized_gibberish(whisper_candidate, norm_lang):
                    translated_text = whisper_candidate
                    logger.info(f"Whisper task=translate produced semantic translation: '{translated_text}'")
            except Exception as w_err:
                logger.warning(f"Whisper translate task error: {w_err}")

        # Print Verbose Diagnostic Log to Terminal
        print("\n" + "=" * 50, flush=True)
        print("=== VOICE DEBUG ===", flush=True)
        print(f"Selected language: {target_lang or 'auto'}", flush=True)
        print(f"Backend language: {norm_lang}", flush=True)
        print(f"Audio MIME: {mime}", flush=True)
        print(f"Audio size: {len(audio_bytes)} bytes", flush=True)
        print(f"Temp Audio Path: {tmp_path}", flush=True)
        print(f"Whisper language: {norm_lang}", flush=True)
        print(f"Whisper task: transcribe", flush=True)
        print(f"RAW TRANSCRIPT:\n{raw_text}", flush=True)
        print(f"TRANSLATION INPUT:\n{raw_text}", flush=True)
        print(f"TRANSLATION OUTPUT:\n{translated_text}", flush=True)
        print("=" * 50 + "\n", flush=True)

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
