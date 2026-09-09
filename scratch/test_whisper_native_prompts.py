"""
Test Whisper STT with Native Script initial_prompts for Telugu, Kannada, and Hindi
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.services.transcription import get_whisper_model
import tempfile
from gtts import gTTS
import whisper

model = whisper.load_model("base")

NATIVE_PROMPTS = {
    "te": "ఆయుర్వేద ఔషధం తయారు చేయడానికి అనుమతులు కావాలి",
    "kn": "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಅನುಮತಿಗಳು ಬೇಕು",
    "hi": "आयुर्वेदिक दवा बनाने के लिए अनुमति चाहिए"
}

TEST_INPUTS = {
    "te": "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?",
    "kn": "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?",
    "hi": "आयुर्वेदिक दवा बनाने के लिए कौन सी अनुमति चाहिए?"
}

for lang, text in TEST_INPUTS.items():
    print(f"\n==================================================")
    print(f"Testing Language: {lang.upper()}")
    print(f"Target Text: {text}")
    print(f"Initial Prompt: {NATIVE_PROMPTS[lang]}")

    tts = gTTS(text=text, lang=lang, slow=False)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(tmp.name)
    tmp_path = tmp.name
    tmp.close()

    res = model.transcribe(
        tmp_path,
        fp16=False,
        task="transcribe",
        language=lang,
        initial_prompt=NATIVE_PROMPTS[lang],
        temperature=0.0,
        condition_on_previous_text=False
    )

    raw_text = res.get("text", "").strip()
    print(f"RAW DECODED TRANSCRIPT:\n{raw_text}")

    devanagari = sum(1 for c in raw_text if '\u0900' <= c <= '\u097f')
    telugu = sum(1 for c in raw_text if '\u0c00' <= c <= '\u0c7f')
    kannada = sum(1 for c in raw_text if '\u0c80' <= c <= '\u0cff')
    print(f"Script Counts -> Telugu: {telugu}, Kannada: {kannada}, Devanagari: {devanagari}")

    os.remove(tmp_path)
