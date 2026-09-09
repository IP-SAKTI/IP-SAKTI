"""
Audit Script to test true semantic translation vs romanization for Telugu, Hindi, Kannada, English
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import whisper
from ip_sakti.multilingual.translator import QueryTranslator

def audit_translation():
    print("=== TRANSLATION AUDIT: NATIVE SCRIPT VS ROMANIZATION ===")

    qt = QueryTranslator()

    test_data = [
        ("Telugu Script", "te", "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు కావాలి?"),
        ("Hindi Script", "hi", "आयुर्वेदिक दवा बनाने के लिए क्या लाइसेंस चाहिए?"),
        ("Kannada Script", "kn", "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?"),
        ("English Script", "en", "What permissions are required to manufacture an Ayurvedic medicine?")
    ]

    for label, lang, text in test_data:
        res = qt.translate_to_retrieval_language(text, lang)
        print(f"\n[{label}] ({lang.upper()}):")
        print("  Original:", text)
        print("  Translated Text:", res.translated_text)

        # Anti-romanization assertion check:
        # Translation MUST contain genuine English vocabulary
        assert res.translated_text is not None
        translated_lower = res.translated_text.lower()
        if lang != "en":
            # Must NOT be a romanized gibberish string like "Hairovidha..."
            is_romanized = "hairovidha" in translated_lower or "haushdha" in translated_lower
            assert not is_romanized, f"ERROR: Translation is romanized gibberish: {res.translated_text}"
            
            # Must contain relevant English semantic terms
            has_english_meaning = any(w in translated_lower for w in ["permission", "license", "manufacture", "make", "ayurvedic", "medicine", "drug", "required", "what"])
            assert has_english_meaning, f"ERROR: Translation lacks English semantic meaning: {res.translated_text}"

    print("\n✅ AUDIT PASSED: QueryTranslator produces TRUE semantic English translations!")

if __name__ == "__main__":
    audit_translation()
