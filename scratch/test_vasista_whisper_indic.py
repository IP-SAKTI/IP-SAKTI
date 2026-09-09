"""
Test fine-tuned Telugu and Kannada models:
vasista22/whisper-telugu-base
vasista22/whisper-kannada-base
"""
import sys
import os
import time
import tempfile
import shutil
import torch
from gtts import gTTS
from transformers import pipeline
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)
target_ffmpeg = os.path.join(ffmpeg_dir, "ffmpeg.exe")
if not os.path.exists(target_ffmpeg) and os.path.exists(ffmpeg_exe):
    shutil.copy2(ffmpeg_exe, target_ffmpeg)
if ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")

print("=== TESTING VASISTA22 FINE-TUNED TELUGU & KANNADA WHISPER MODELS ===")

# Test 1: Telugu fine-tuned model
print("\n--- 1. Testing vasista22/whisper-telugu-base ---")
telugu_text = "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"
tts = gTTS(text=telugu_text, lang="te", slow=False)
tmp_te = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
tts.save(tmp_te.name)
tmp_te_path = tmp_te.name
tmp_te.close()

try:
    t0 = time.time()
    pipe_te = pipeline(
        "automatic-speech-recognition",
        model="vasista22/whisper-telugu-base",
        torch_dtype=torch.float32,
        device="cpu"
    )
    res_te = pipe_te(tmp_te_path)
    elapsed_te = time.time() - t0
    print(f"Time Taken: {elapsed_te:.2f}s")
    print(f"Telugu RAW TRANSCRIPT: {res_te.get('text', '')!r}")
except Exception as e:
    print(f"Telugu model error: {e}")
finally:
    if os.path.exists(tmp_te_path):
        os.remove(tmp_te_path)

# Test 2: Kannada fine-tuned model
print("\n--- 2. Testing vasista22/whisper-kannada-base ---")
kannada_text = "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"
tts = gTTS(text=kannada_text, lang="kn", slow=False)
tmp_kn = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
tts.save(tmp_kn.name)
tmp_kn_path = tmp_kn.name
tmp_kn.close()

try:
    t0 = time.time()
    pipe_kn = pipeline(
        "automatic-speech-recognition",
        model="vasista22/whisper-kannada-base",
        torch_dtype=torch.float32,
        device="cpu"
    )
    res_kn = pipe_kn(tmp_kn_path)
    elapsed_kn = time.time() - t0
    print(f"Time Taken: {elapsed_kn:.2f}s")
    print(f"Kannada RAW TRANSCRIPT: {res_kn.get('text', '')!r}")
except Exception as e:
    print(f"Kannada model error: {e}")
finally:
    if os.path.exists(tmp_kn_path):
        os.remove(tmp_kn_path)

