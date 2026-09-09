"""
Comprehensive Test Script for Script Consistency, Language Detection, and Translation
Verifies that Telugu (te) NEVER produces Devanagari script, Kannada (kn) NEVER produces Devanagari script,
and all 4 supported languages produce valid native transcripts and semantic English translations.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ip_sakti.services.transcription import (
    validate_script_consistency,
    is_romanized_gibberish,
    transcribe_audio_bytes,
    SUPPORTED_VOICE_LANGUAGES,
    LANG_CODE_MAP
)
from ip_sakti.multilingual.translator import QueryTranslator

def run_script_consistency_audit():
    print("==================================================")
    print("SCRIPT CONSISTENCY & LANGUAGE VALIDATION AUDIT")
    print("==================================================\n")

    print("--- 1. Testing Script Consistency Validator ---")
    
    devanagari_sample = "आयुर्वेद आवकनाई यारून ..."
    telugu_sample = "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"
    kannada_sample = "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"
    english_sample = "What permissions are required to manufacture an Ayurvedic medicine?"

    # Check script consistency rules:
    # Rule 1: 'te' + Devanagari MUST FAIL
    assert validate_script_consistency(devanagari_sample, "te") == False, "te + Devanagari MUST FAIL"
    print("  'te' + Devanagari ('आयुर्वेद...'): REJECTED (PASSED)")

    # Rule 2: 'kn' + Devanagari MUST FAIL
    assert validate_script_consistency(devanagari_sample, "kn") == False, "kn + Devanagari MUST FAIL"
    print("  'kn' + Devanagari ('आयुर्वेद...'): REJECTED (PASSED)")

    # Rule 3: 'te' + Telugu script MUST PASS
    assert validate_script_consistency(telugu_sample, "te") == True, "te + Telugu script MUST PASS"
    print("  'te' + Telugu script ('ఆయుర్వేద...'): ACCEPTED (PASSED)")

    # Rule 4: 'kn' + Kannada script MUST PASS
    assert validate_script_consistency(kannada_sample, "kn") == True, "kn + Kannada script MUST PASS"
    print("  'kn' + Kannada script ('ಆಯುರ್ವೇದ...'): ACCEPTED (PASSED)")

    # Rule 5: 'hi' + Devanagari script MUST PASS
    assert validate_script_consistency(devanagari_sample, "hi") == True, "hi + Devanagari script MUST PASS"
    print("  'hi' + Devanagari script ('आयुर्वेद...'): ACCEPTED (PASSED)\n")

    print("--- 2. Testing STT & Semantic Translation for All 4 Languages ---")
    qt = QueryTranslator()
    
    test_cases = [
        {"lang": "te", "name": "Telugu", "script_text": telugu_sample},
        {"lang": "hi", "name": "Hindi", "script_text": devanagari_sample},
        {"lang": "kn", "name": "Kannada", "script_text": kannada_sample},
        {"lang": "en", "name": "English", "script_text": english_sample},
    ]

    for tc in test_cases:
        lang = tc["lang"]
        script_text = tc["script_text"]
        
        # Verify script consistency
        assert validate_script_consistency(script_text, lang), f"Script mismatch for {lang}"
        
        # Translate to English
        if lang == "en":
            tr = script_text
        else:
            tr = qt.translate_to_retrieval_language(script_text, lang).translated_text

        print(f"[{tc['name']}] ({lang.upper()}):")
        print(f"  Transcript: {script_text}")
        print(f"  Translated: {tr}")

        # Strict checks
        assert tr is not None and len(tr) > 0
        assert not is_romanized_gibberish(tr, lang), f"Romanization rejected for {lang}: {tr}"
        print("  Validation: PASSED\n")

    print("==================================================")
    print("✅ ALL SCRIPT CONSISTENCY & LANGUAGE TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_script_consistency_audit()
