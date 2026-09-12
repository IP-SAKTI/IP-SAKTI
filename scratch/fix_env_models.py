"""
scratch/fix_env_models.py

Safely update .env file to set:
GEMINI_MODEL=gemini-3.6-flash
GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts
without exposing secrets.
"""

from pathlib import Path

env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    lines = env_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    has_model = False
    has_tts_model = False
    
    for line in lines:
        if line.startswith("GEMINI_MODEL="):
            new_lines.append("GEMINI_MODEL=gemini-3.6-flash")
            has_model = True
        elif line.startswith("GEMINI_TTS_MODEL="):
            new_lines.append("GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts")
            has_tts_model = True
        else:
            new_lines.append(line)
            
    if not has_model:
        new_lines.append("GEMINI_MODEL=gemini-3.6-flash")
    if not has_tts_model:
        new_lines.append("GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts")
        
    env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(".env updated successfully: GEMINI_MODEL=gemini-3.6-flash")
else:
    print(".env file not found!")
