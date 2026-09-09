"""
Test Whisper Telugu decoding with initial_prompt and language settings
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.services.transcription import get_whisper_model, validate_script_consistency
import tempfile
from gtts import gTTS
import whisper

telugu_text = "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"

# Generate audio
tts = gTTS(text=telugu_text, lang="te", slow=False)
tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
tts.save(tmp.name)
tmp_path = tmp.name
tmp.close()

print(f"Generated Telugu Audio at: {tmp_path}")

model = whisper.load_model("base")

prompts_to_test = [
    None,
    "తెలుగు:",
    "ఆయుర్వేద ఔషధం తయారు చేయడం అనుమతి",
    "ఈ క్రింది ప్రశ్న తెలుగు భాషలో ఇవ్వబడింది:",
    "Telugu script transcription in Telugu (తెలుగు):"
]

for prompt in prompts_to_test:
    print("\n" + "=" * 60)
    print(f"Testing initial_prompt: {prompt!r}")
    
    kwargs = {
        "fp16": False,
        "task": "transcribe",
        "language": "te",
        "temperature": 0.0,
        "condition_on_previous_text": False,
    }
    if prompt:
        kwargs["initial_prompt"] = prompt

    res = model.transcribe(tmp_path, **kwargs)
    raw = res.get("text", "").strip()
    
    devanagari = sum(1 for c in raw if '\u0900' <= c <= '\u097f')
    telugu = sum(1 for c in raw if '\u0c00' <= c <= '\u0c7f')
    arabic = sum(1 for c in raw if '\u0600' <= c <= '\u06ff')
    latin = sum(1 for c in raw if 'a' <= c.lower() <= 'z')

    print(f"RAW TRANSCRIPT: {raw!r}")
    print(f"Counts -> Telugu: {telugu}, Devanagari: {devanagari}, Arabic/Urdu: {arabic}, Latin: {latin}")

os.remove(tmp_path)
