"""
Voice Input / Speech-to-Text Transcription Service for IP-SAKTI Sahayak

Uses pretrained Whisper (openai-whisper) with lightweight model ('tiny' or 'base')
for low latency CPU transcription supporting English and Indian languages.
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


def get_whisper_model(model_name: str = "tiny"):
    """
    Lazy-load and return cached singleton instance of Whisper model.
    Default: 'tiny' for fast CPU inference.
    """
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        logger.info(f"Loading Whisper model '{model_name}'...")
        import whisper
        _WHISPER_MODEL = whisper.load_model(model_name)
        logger.info(f"Whisper model '{model_name}' loaded successfully.")
    return _WHISPER_MODEL


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe audio bytes using pretrained Whisper model.
    
    Args:
        audio_bytes: Raw bytes of the recorded audio file.
        filename: Original filename or hint for format extension.
        
    Returns:
        dict: {"transcript": str, "language": str, "error": str | None}
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return {
            "transcript": "",
            "language": "en",
            "error": "Audio recording is empty or too short. Please speak again."
        }

    ext = os.path.splitext(filename)[1]
    if not ext or len(ext) > 10:
        ext = ".webm"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_whisper_model("tiny")
        # Transcribe temporary audio file with CPU fallback (fp16=False)
        result = model.transcribe(tmp_path, fp16=False)
        text = result.get("text", "").strip()
        language = result.get("language", "en")

        logger.info(f"Transcribed audio ({len(audio_bytes)} bytes) -> '{text}' (lang={language})")

        return {
            "transcript": text,
            "language": language,
            "error": None if text else "No speech detected in audio. Please try speaking clearly."
        }
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}", exc_info=True)
        return {
            "transcript": "",
            "language": "en",
            "error": f"Transcription failed: {str(e)}"
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
